#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@File         :heybox_lib/thdlib/kafka/client
@Description  :kafka增强消费者
@Date         :2022/11/3 2:43 PM
@Author       :Sikai Lin
@Runs on      : 
"""
import json
import signal

from enum import IntEnum
from queue import Queue, Empty
from heybox_lib.conf import config
from typing import List, Callable
from confluent_kafka import Consumer, TopicPartition
from heybox_lib.logger import log
from heybox_lib.rpc.proto import heybox_producer_v2
from concurrent.futures import ThreadPoolExecutor

log.init_logger()

if config.DEBUG:
    hash_len = 5
else:
    hash_len = 100


def bkd_hash(_word) -> int:
    seed = 131
    _hash = 0
    for ca in _word:
        _hash = _hash * seed + ord(ca)
    return _hash % hash_len


class ConsumeStatus(IntEnum):
    SUCCESS = 0
    FAILURE = 1


class RetryMode(IntEnum):
    NO_RETRY = 0
    SEEK_ONLY = 1
    SEEK_QUEUE = 2


class KafkaAtLeastOnceConsumer(object):
    """
    注意：用户消息内容不得包含以__开头的关键字，例如：__retry、__topic

    """

    run_flag = True
    # seek消息重复消费map，str(topic + partition + offset) -> try_count
    try_map = {}

    def __init__(
            self,
            group_id: str,
            topic_list: List,
            user_function: Callable,
            servers: List = config.KAFKA_HOST,
            reset_type: str = 'latest',
            concurrency: int = 5,
            batch_size: int = 10,
            timeout: int = 1,
            mode: int = None,
            seek_retry_limit: int = 2,
            queue_retry_limit: int = 0,
            consumer_config: dict = {},
            consume_multi: bool = False,
    ):
        """
        参数解释

        group_id: 消费者组id
        topic_list: 监听的topic列表
        user_function: 用户的可调用函数
        servers: the list of kafka broker
        reset_type: 当找不到消费偏移量时重置偏移量的策略
        concurrency: 并发度，处理一批消息使用多少个线程并发处理
        batch_size: 吞吐量，每批待处理消息的个数
        timeout: 获取消息的超时时间，单位秒
        mode: 设置模式，参见 RetryMode
        seek_retry_cnt: 使用seek重试次数
        queue_retry_cnt: 使用重试队列重试次数
        consume_multi: 用户函数是否为批处理函数
        """

        assert concurrency > 0, '消费者并发度须大于0'
        assert batch_size >= concurrency, '单批消息数须大于等于并发度'
        assert timeout > 0, '获取消息超时时间须大于0'
        assert seek_retry_limit > -2, 'seek重试次数应大于等于-1'
        assert queue_retry_limit > -2, '重试队列重试次数应大于等于-1'
        for _topic in topic_list:
            assert isinstance(_topic, str), '订阅topic列表必须均为字符串'
            assert not _topic.startswith('kfk_retry_queue_'), '订阅topic不能以kfk_retry_queue_开头'

        self._servers = ','.join(servers)
        self._group_id = group_id
        self._user_function = user_function
        self._reset_type = reset_type
        self._topic_list = topic_list
        self._concurrency = concurrency
        self._batch_size = batch_size
        self._timeout = timeout
        self._seek_retry_limit = seek_retry_limit
        self._queue_retry_limit = queue_retry_limit
        self._consumer_config = consumer_config
        self._consume_multi = consume_multi

        if mode == RetryMode.NO_RETRY:
            self._seek_retry_limit = 0
            self._queue_retry_limit = 0
        elif mode == RetryMode.SEEK_ONLY:
            self._queue_retry_limit = 0

        if self._queue_retry_limit != 0:
            self.grpc_producer = heybox_producer_v2.Client(retry=True)

            _temp_list = []
            for _topic in self._topic_list:
                _temp_list.append('kfk_retry_queue_' + str(bkd_hash(_topic)))
            self._topic_list.extend(_temp_list)
            self._topic_list = list(set(self._topic_list))

    def start(self) -> None:
        def _sig_handler(signum, _):  # noqa: U101
            log.info(f"Receive {signum=}, prepare to shutdown")
            self.shutdown()

        signal.signal(signal.SIGINT, _sig_handler)
        signal.signal(signal.SIGTERM, _sig_handler)
        self._core()

    def shutdown(self) -> None:
        KafkaAtLeastOnceConsumer.run_flag = False

    def _core(self) -> None:
        consumer = None
        batch_pool = None
        try:
            consumer = self._init_consumer()
            process_queue = Queue()
            error_queue = Queue()
            if not self._consume_multi:
                batch_pool = ThreadPoolExecutor(max_workers=self._concurrency)
                for _ in range(self._concurrency):
                    batch_pool.submit(self._thread_run, process_queue, error_queue)
            while KafkaAtLeastOnceConsumer.run_flag:
                msgs = consumer.consume(num_messages=self._batch_size, timeout=self._timeout)
                if not msgs:
                    continue
                need_store_map = {}
                for _msg in msgs:
                    if _msg.error():
                        log.exception(_msg.error())
                        continue
                    t, p, o = _msg.topic(), _msg.partition(), _msg.offset()
                    map_key = t + str(p)
                    if need_store_map.get(map_key) is None or o >= need_store_map[map_key].offset:
                        need_store_map[map_key] = TopicPartition(t, partition=p, offset=o+1)
                    if not self._consume_multi:
                        process_queue.put(_msg)
                if self._consume_multi:
                    self._multi_process(msgs, error_queue)
                else:
                    process_queue.join()
                question_map = {}
                while not error_queue.empty():
                    try:
                        item = error_queue.get(block=False)
                        _msg, _type = item['msg'], item['type']
                        if _type == 'seek':
                            t, p, o = _msg.topic(), _msg.partition(), _msg.offset()
                            map_key = t + str(p)
                            if question_map.get(map_key) is None or o < question_map.get(map_key).offset:
                                question_map[map_key] = TopicPartition(t, partition=p, offset=o)
                            if map_key in need_store_map and o < need_store_map[map_key].offset:
                                need_store_map[map_key] = TopicPartition(t, partition=p, offset=o)
                        else:
                            _destination = 'kfk_retry_queue_' + str(bkd_hash(_msg['__topic']))
                            self.grpc_producer.grpc_kafka_producer_v2(_destination, [json.dumps(_msg)])
                        error_queue.task_done()
                    except Empty:
                        break
                if question_map:
                    for _topic_partition in question_map.values():
                        consumer.seek(_topic_partition)
                if need_store_map.values():
                    consumer.store_offsets(offsets=list(need_store_map.values()))

        except Exception as e:
            log.exception(e)
        finally:
            KafkaAtLeastOnceConsumer.run_flag = False
            try:
                if consumer:
                    consumer.close()
                if batch_pool:
                    batch_pool.shutdown()
            except Exception as e:
                log.exception(e)

    def _multi_process(self, msgs, error_queue):
        try:
            # 1、解析消息
            msg_list = []
            new_msgs = []
            for msg in msgs:
                is_skip, _content, _topic, _partition, _offset, _queue_cnt, _key, _seek_cnt, msg = self._resolve(msg)
                if is_skip:
                    continue
                new_msgs.append(msg)
                msg_list.append((_content, _topic, _partition, _offset, _queue_cnt, _key, _seek_cnt, msg))
            if not new_msgs:
                return

            # 2、执行用户函数，并获取执行结果
            try:
                func_returns = self._user_function(new_msgs)
            except Exception:
                func_returns = [ConsumeStatus.FAILURE] * len(new_msgs)
            for idx, msg_t in enumerate(msg_list):
                if idx < len(func_returns):
                    func_return = func_returns[idx]
                else:
                    func_return = ConsumeStatus.SUCCESS
                if func_return not in [ConsumeStatus.SUCCESS, ConsumeStatus.FAILURE]:
                    func_return = ConsumeStatus.SUCCESS

                self._do_action(func_return, error_queue, msg_t)
        except Exception as e:
            log.exception(e)

    def _resolve(self, msg):
        """解析消息，抹平重试消息与普通消息的差异"""
        msg_data = json.loads(msg.value().decode('utf-8'))
        _queue_cnt = 0
        if isinstance(msg_data, dict) and '__topic' in msg_data:
            # 重试消息
            _content = msg_data['__msg']
            _topic = msg_data['__topic']
            _partition = msg_data['__partition']
            _offset = msg_data['__offset']
            _queue_cnt = msg_data['__retry']
            if _topic not in self._topic_list:
                return True, None, None, None, None, None, None, None, None
            msg.set_value(_content.encode('utf-8'))
        else:
            # 普通消息
            _content = msg.value().decode('utf-8')
            _topic = msg.topic()
            _partition = msg.partition()
            _offset = msg.offset()

        _key = _topic + str(_partition) + str(_offset)
        _seek_cnt = KafkaAtLeastOnceConsumer.try_map.get(_key, 0)
        return False, _content, _topic, _partition, _offset, _queue_cnt, _key, _seek_cnt, msg

    def _do_action(self, func_return, error_queue, msg_t) -> None:
        """根据执行结果执行相应动作"""
        _content, _topic, _partition, _offset, _queue_cnt, _key, _seek_cnt, msg = msg_t
        if func_return == ConsumeStatus.SUCCESS:
            KafkaAtLeastOnceConsumer.try_map.pop(_key, None)
        else:
            if self._seek_retry_limit == -1 or self._seek_retry_limit > _seek_cnt:
                error_queue.put({"msg": msg, "type": "seek"})
                KafkaAtLeastOnceConsumer.try_map[_key] = _seek_cnt + 1
            elif self._queue_retry_limit == -1 or self._queue_retry_limit > _queue_cnt:
                new_content = {
                    '__msg': _content,
                    '__topic': _topic,
                    '__partition': _partition,
                    '__offset': _offset,
                    '__retry': _queue_cnt + 1,
                }
                error_queue.put({"msg": new_content, "type": "queue"})
            else:
                KafkaAtLeastOnceConsumer.try_map.pop(_key, None)

    def _thread_run(self, process_queue: Queue, error_queue: Queue) -> None:
        while True:
            try:
                # 1、读取消息
                try:
                    msg = process_queue.get(timeout=1)
                except Empty:
                    if KafkaAtLeastOnceConsumer.run_flag:
                        continue
                    else:
                        break

                # 2、解析消息
                is_skip, _content, _topic, _partition, _offset, _queue_cnt, _key, _seek_cnt, msg = self._resolve(msg)
                if is_skip:
                    process_queue.task_done()
                    continue

                # 3、执行用户函数，并获取执行结果
                try:
                    func_return = self._user_function(msg)
                except Exception:
                    func_return = ConsumeStatus.FAILURE
                if func_return not in [ConsumeStatus.SUCCESS, ConsumeStatus.FAILURE]:
                    func_return = ConsumeStatus.SUCCESS

                # 4、根据执行结果执行相应动作
                self._do_action(
                    func_return,
                    error_queue,
                    (_content, _topic, _partition, _offset, _queue_cnt, _key, _seek_cnt, msg),
                )
                process_queue.task_done()
            except Exception as e:
                log.exception(e)
                try:
                    process_queue.task_done()
                except Exception as e:
                    log.exception(e)

    def _init_consumer(self) -> Consumer:
        self._consumer_config.update(
            {
                'bootstrap.servers': self._servers,
                'group.id': self._group_id,
                'auto.offset.reset': self._reset_type,
                'enable.auto.offset.store': False,
            }
        )
        _consumer = Consumer(self._consumer_config)
        _consumer.subscribe(self._topic_list)
        return _consumer
