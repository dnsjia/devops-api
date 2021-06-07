#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
@Time: 2021/4/16 0016 下午 12:49
@Author: micheng. <safemonitor@outlook.com>
@File: my_exception.py
"""


class AkException(BaseException):
    def __init__(self, *args, **kwargs):  # real signature unknown
        pass

    def __str__(self):
        return "获取阿里云AK失败！"


class AnsibleError(Exception):
    pass
