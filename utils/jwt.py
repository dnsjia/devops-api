#!/bin/env python3
# -*- coding: utf-8 -*-

"""
@Time: 2020/9/27 18:30
@Author: yu.jiang <safemonitor@outlook.com>
@License: Apache License
@File: jwt.py

"""


def jwt_response_payload_handler(token, user=None, request=None):
    return {
        "token": token,
        "id": user.user_id,
        "name": user.name,
        "avatar": user.avatar,
        "errcode": 0,
        "msg": "登录成功"
    }
