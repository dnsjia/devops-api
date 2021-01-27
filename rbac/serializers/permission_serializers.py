#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : permission_serializers.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2020/12/1
# @Desc  :
from rest_framework import serializers
from rbac.models import Permission


class PermissionSerializer(serializers.ModelSerializer):
    """
    权限列化
    """

    class Meta:
        model = Permission
        fields = '__all__'
