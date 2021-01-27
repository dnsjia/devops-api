#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : menu_serializers.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2020/12/1
# @Desc  :
from rest_framework import serializers
from rbac.models import Menu


class MenuSerializer(serializers.ModelSerializer):
    """
    角色列表序列化
    """

    class Meta:
        model = Menu
        fields = '__all__'
