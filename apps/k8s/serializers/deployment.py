#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
# @File  : deployment.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2020/12/7
# @Desc  :
"""

from rest_framework import serializers


class DeploymentSerializers(serializers.Serializer):
    """
    Deployment的序列化
    """
    namespace = serializers.CharField()
    name = serializers.CharField()
    labels = serializers.JSONField()
    create_time = serializers.DateTimeField()
    image = serializers.CharField()
    replicas = serializers.CharField()
    available_replicas = serializers.CharField()
    ready_replicas = serializers.CharField()
    unavailable_replicas = serializers.CharField()
    updated_replicas = serializers.CharField()
