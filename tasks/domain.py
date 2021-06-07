#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
@Time: 2021/4/14 0014 下午 1:38
@Author: micheng. <safemonitor@outlook.com>
@File: domain.py
"""


from celery import shared_task


@shared_task
def sync_domain():
    print("10s 同步一次域名")
    return "10s 同步一次域名"