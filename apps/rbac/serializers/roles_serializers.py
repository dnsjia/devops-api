#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
# @File  : roles_serializers.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2020/12/1
# @Desc  :
"""

from rest_framework import serializers
from apps.rbac.models import Role


class RoleListSerializer(serializers.ModelSerializer):
    """
    角色列表序列化
    """

    class Meta:
        model = Role
        fields = '__all__'
        depth = 1


class RoleModifySerializer(serializers.ModelSerializer):
    """
    角色增删改序列化
    """

    title = serializers.CharField(required=False)

    class Meta:
        model = Role
        fields = '__all__'

