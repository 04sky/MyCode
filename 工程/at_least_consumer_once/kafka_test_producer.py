#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@File         :heybox_lib/thdlib/test/kafka_producer_test
@Description  :
@Date         :2022/11/8 2:12 PM
@Author       :Sikai Lin
@Runs on      : 
"""

import json
import time

from confluent_kafka import Producer

from heybox_lib.conf import config

p = Producer(
    {
        'bootstrap.servers': ','.join(config.KAFKA_HOST),
    }
)
total_count = 0
c = 0
try:
    for i in range(10000):
        a = {'t': i, 'time': time.time()}
        p.produce('test-topic-vv', json.dumps(a))
        c += 1
        if c % 100 == 0:
            p.flush()

finally:
    p.flush()
