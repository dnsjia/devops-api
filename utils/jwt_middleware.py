#!/bin/env python3
# -*- coding: utf-8 -*-

"""
@Time: 2020/9/28 17:53
@Author: yu.jiang <safemonitor@outlook.com>
@License: Apache License
@File: jwt_middleware.py

"""

from rest_framework.exceptions import AuthenticationFailed
from rest_framework_jwt.serializers import VerifyJSONWebTokenSerializer


class TokenAuth():
    def authenticate(self, request):
        token = {"token": None}
        token["token"] = request.META.get('HTTP_TOKEN')
        valid_data = VerifyJSONWebTokenSerializer().validate(token)
        print(valid_data)
        user = valid_data['user']
        print(user)
        if user:
            return
        else:
            raise AuthenticationFailed('认证失败')
