#!/bin/env python3
# -*- coding: utf-8 -*-

"""
@Time: 2020/9/27 13:01
@Author: yu.jiang <safemonitor@outlook.com>
@License: Apache License
@File: token.py

"""

import hashlib
import time


def md5(username):
    """
    生成用户token
    :param username:
    :return: token
    """
    ctime = str(time.time())
    m = hashlib.md5(bytes(username, encoding='utf-8'))
    m.update(bytes(ctime, encoding='utf-8'))
    return m.hexdigest()
