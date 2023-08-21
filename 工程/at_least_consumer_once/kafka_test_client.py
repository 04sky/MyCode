#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@File         :heybox_lib/thdlib/test/kafka_client_v2_test
@Description  :
@Date         :2022/12/9 6:52 PM
@Author       :Sikai Lin
@Runs on      :
"""
import sys
import random
import time
import json

from heybox_lib.thdlib.kafka.client import KafkaAtLeastOnceConsumer, ConsumeStatus, RetryMode
from heybox_lib.logger import log

log.init_logger()

group_id = 'test-topic-consumer-group'
topic = 'test-topic-vv'


def _get_msg_data(msg):
    p = msg.partition()
    o = msg.offset()
    t = msg.topic()
    value = json.loads(msg.value().decode('utf-8'))
    return p, o, t, value


def my_function(msg):
    if msg.error():
        log.error('fetch msg is error. error:%s' % msg.error())
        return ConsumeStatus.FAILURE
    # 处理业务逻辑，单次问题进行重试
    p, o, t, value = _get_msg_data(msg)
    if random.randint(1, 100) == 9:
        log.info("发生业务异常返回False, topic:%s, partition:%s,  offset %s, value:%s " % (t, p, o, value))
        return ConsumeStatus.FAILURE
    else:
        log.info('业务处理消息, topic:%s, partition:%s,  offset %s, value:%s ' % (t, p, o, value))
        return ConsumeStatus.SUCCESS


def my_multi_function(msgs):
    function_returns = []
    for msg in msgs:
        if msg.error():
            log.error('fetch msg is error. error:%s' % msg.error())
            function_returns.append(ConsumeStatus.FAILURE)
        # 处理业务逻辑，单次问题进行重试
        p, o, t, value = _get_msg_data(msg)
        if random.randint(1, 100) == 9:
            log.info("发生业务异常返回False, topic:%s, partition:%s,  offset %s, value:%s " % (t, p, o, value))
            function_returns.append(ConsumeStatus.FAILURE)
        else:
            log.info('业务处理消息, topic:%s, partition:%s,  offset %s, value:%s ' % (t, p, o, value))
            function_returns.append(ConsumeStatus.SUCCESS)
    return function_returns


def success_function(msg):
    # 处理业务逻辑，完全正常
    if msg.error():
        log.error('fetch msg is error. error:%s' % msg.error())
        return ConsumeStatus.FAILURE
    p, o, t, value = _get_msg_data(msg)
    log.info('业务处理消息，, topic:%s, partition:%s,  offset %s, value:%s ' % (t, p, o, value))
    return ConsumeStatus.SUCCESS


def exception_function(msg):
    # 处理业务逻辑，抛出异常重试
    if msg.error():
        log.error('fetch msg is error. error:%s' % msg.error())
        return ConsumeStatus.FAILURE
    p, o, t, value = _get_msg_data(msg)
    if random.randint(1, 100) == 9:
        log.info("发生业务异常返回False, , topic:%s, partition:%s,  offset %s, value:%s " % (t, p, o, value))
        raise Exception('业务异常')
    else:
        log.info('业务处理消息，, topic:%s, partition:%s,  offset %s, value:%s ' % (t, p, o, value))
        return ConsumeStatus.SUCCESS


def test_normal_try_limit(mode):
    consumer = KafkaAtLeastOnceConsumer(group_id, [topic], my_function, mode=mode)
    consumer.start()


def test_multi_try_limit(mode):
    consumer = KafkaAtLeastOnceConsumer(group_id, [topic], my_multi_function, mode=mode, consume_multi=True)
    consumer.start()


def test_normal_any_way(seek_limit, queue_limit):
    consumer = KafkaAtLeastOnceConsumer(group_id, [topic], my_function, seek_retry_limit=seek_limit, queue_retry_limit=queue_limit)
    consumer.start()


def test_exception_try_limit(mode):
    # 异常指定重试次数(-1无限/数字为重试次数)
    consumer = KafkaAtLeastOnceConsumer(group_id, [topic], exception_function, mode=mode)
    consumer.start()


def test_crash_consume():
    # 模拟消费者关停/崩溃，消费者继续消费
    consumer = KafkaAtLeastOnceConsumer(group_id, [topic], success_function)
    consumer.start()
    time.sleep(20)
    consumer.shutdown()


def test_with_consumer_config():
    # 执行将报错，证明配配置可行：Failed to create consumer: `max.poll.interval.ms`must be >= `session.timeout.ms`"}
    consumer_config = {
        "session.timeout.ms": 60000,
        "max.poll.interval.ms": 35000,
        "fetch.wait.max.ms": 1000,
    }
    consumer = KafkaAtLeastOnceConsumer(group_id, [topic], my_function, consumer_config=consumer_config)
    consumer.start()


if __name__ == '__main__':
    test_channel = sys.argv[1]

    if test_channel == "1":
        test_normal_try_limit(RetryMode.SEEK_ONLY)
    elif test_channel == "2":
        test_normal_try_limit(RetryMode.SEEK_QUEUE)
    elif test_channel == "3":
        test_normal_try_limit(RetryMode.NO_RETRY)
    elif test_channel == "4":
        test_normal_any_way(0, 2)
    elif test_channel == "5":
        test_normal_any_way(-1, 2)
    elif test_channel == "6":
        test_normal_any_way(0, -1)
    elif test_channel == "7":
        test_exception_try_limit(RetryMode.SEEK_QUEUE)
    elif test_channel == "8":
        test_crash_consume()
    elif test_channel == "9":
        test_with_consumer_config()
    elif test_channel == "10":
        test_multi_try_limit(RetryMode.NO_RETRY)
    elif test_channel == "11":
        test_multi_try_limit(RetryMode.SEEK_ONLY)
    elif test_channel == "12":
        test_normal_try_limit(RetryMode.SEEK_QUEUE)
    else:
        test_normal_try_limit(-1)

