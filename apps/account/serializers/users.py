#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
# @File  : users.py
# @Author: 往事随风
# @Email: gujiwork@outlook.com
# @Date  : 2021/5/28
# @Desc  :
"""

from rest_framework import serializers
from apps.account.models import User


class UserInfoSerializer(serializers.ModelSerializer):
    """
    用户信息
    """

    class Meta:
        model = User
        fields = ["id", "username", "email", "user_id", "mobile", "name", "sex", "position",
                  "avatar", "is_active", "last_login", "roles", "is_staff"
                  ]
        depth = 1
