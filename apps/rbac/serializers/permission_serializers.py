#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
# @File  : permission_serializers.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2020/12/1
# @Desc  :
"""

from rest_framework import serializers
from apps.rbac.models import Permission


class PermissionSerializer(serializers.ModelSerializer):
    """
    权限列化
    """

    class Meta:
        model = Permission
        fields = '__all__'
