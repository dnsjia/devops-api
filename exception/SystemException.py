#!/bin/env python3
# -*- coding: utf-8 -*-

"""
@Time: 2020/9/28 13:39
@Author: yu.jiang <safemonitor@outlook.com>
@License: Apache License
@File: SystemException.py

"""

from rest_framework.exceptions import APIException


class ServiceUnavailable(APIException):
    status_code = 200
    default_detail = {
        "errcode": "1006",
        "msg": "系统异常, 请刷新重试!",
        "data": "null"
    }
    default_code = "service_unavaliable"