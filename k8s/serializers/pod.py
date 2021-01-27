#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : pod.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2020/12/7
# @Desc  :
from rest_framework import serializers


class PodSerializers(serializers.Serializer):
    """
    Pod的序列化
    """
    pod_ip = serializers.IPAddressField()
    namespace = serializers.CharField()
    name = serializers.CharField()
    host_ip = serializers.IPAddressField()
    status = serializers.CharField()
    create_time = serializers.DateTimeField()
    restart_count = serializers.CharField()