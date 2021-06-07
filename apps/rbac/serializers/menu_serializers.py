#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
# @File  : menu_serializers.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2020/12/1
# @Desc  :
"""

from rest_framework import serializers
from apps.rbac.models import Menu


class MenuSerializer(serializers.ModelSerializer):
    """
    角色列表序列化
    """

    class Meta:
        model = Menu
        fields = '__all__'
