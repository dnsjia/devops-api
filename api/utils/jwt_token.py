#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : jwt_token.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2020/12/1
# @Desc  :
import jwt
import datetime
from jwt import exceptions
from django.conf import settings
from api.models import UserInfo
import logging
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
    result = {'status': False, 'data': None, 'error': None}
    try:
        verified_payload = jwt.decode(token, JWT_SALT, True)
        result['status'] = True
        result['data'] = verified_payload
    except exceptions.ExpiredSignatureError:
        result['error'] = 'token已失效'
    except jwt.DecodeError:
        result['error'] = 'token认证失败'
    except jwt.InvalidTokenError:
        result['error'] = '非法的token'
    return result