#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
# @File  : jwt_token.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2020/12/1
# @Desc  :
"""

import datetime
import logging

import jwt
from jwt import exceptions
from django.conf import settings

logger = logging.getLogger('default')

JWT_SALT = settings.SECRET_KEY


def create_token(payload, timeout=20):
    """
    :param payload:  例如：{'id':1,'username':'xiaoming'}用户信息
    :param timeout: token的过期时间，默认20分钟
    :return: token
    """
    headers = {
        'typ': 'jwt',
        'alg': 'HS256'
    }
    logger.info('开始创建Token--->', payload)
    payload['exp'] = datetime.datetime.utcnow() + datetime.timedelta(minutes=timeout)
    result = jwt.encode(payload=payload, key=JWT_SALT, algorithm="HS256", headers=headers).decode('utf-8')
    return result


def parse_payload(token):
    """
    对token进行和发行校验并获取payload
    :param token: token
    :return: 用户信息
    """
    result = {'status': False, 'data': None, 'errmsg': None}
    try:
        verified_payload = jwt.decode(token, JWT_SALT, True)
        result['status'] = True
        result['data'] = verified_payload
    except exceptions.ExpiredSignatureError:
        result['errmsg'] = 'token已失效'
    except jwt.DecodeError:
        result['errmsg'] = 'token认证失败'
    except jwt.InvalidTokenError:
        result['errmsg'] = '非法的token'
    return result
