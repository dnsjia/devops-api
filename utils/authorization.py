#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
# @File  : authorization.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2020/12/14
# @Desc  :
"""

import logging

from rest_framework import status
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from apps.account.models import User
from utils.jwt_token import parse_payload

logger = logging.getLogger('default')


class MyAuthentication(BaseAuthentication):
    """
    token认证
    """

    def authenticate(self, request):

        authorization = request.META.get('HTTP_AUTHORIZATION', '')
        auth = authorization.split()
        if not auth:
            raise AuthenticationFailed({'msg': '未获取到Authorization请求头', 'status': 403})
        if auth[0].lower() != 'jwt':
            raise AuthenticationFailed({'msg': 'Authorization请求头中认证方式错误', 'status': 403})
        if len(auth) == 1:
            raise AuthenticationFailed({'msg': "非法Authorization请求头", 'status': 403})
        elif len(auth) > 2:
            raise AuthenticationFailed({'msg': "非法Authorization请求头", 'status': 403})
        token = auth[1]
        result = parse_payload(token)

        if not result['status']:
            raise AuthenticationFailed(result)

        try:
            user = User.objects.get(username=result['data'].get('username'))
        except User.DoesNotExist:
            raise AuthenticationFailed('User does not exist')
        return user, token

    def authenticate_header(self, request):
        return status.HTTP_401_UNAUTHORIZED
