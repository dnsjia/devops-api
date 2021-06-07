#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
# @File  : node.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2021/4/4
# @Desc  :
"""

from rest_framework import serializers


class NodeSerializers(serializers.Serializer):
    """
    Node序列化
    """
    host = serializers.IPAddressField()
    hostname = serializers.CharField()
    name = serializers.CharField()
    labels = serializers.JSONField()
    allocatable = serializers.JSONField()
    capacity = serializers.JSONField()
    status = serializers.CharField()
    unschedule = serializers.CharField()
    allocated_pods = serializers.IntegerField()
    node_info = serializers.JSONField()
    creation_timestamp = serializers.DateTimeField()
    conditions = serializers.JSONField()
    resouces = serializers.JSONField()

    # node_all_label = serializers.JSONField()
    # cpu_alloc = serializers.CharField()
    # cpu_req = serializers.CharField()
    # cpu_lmt = serializers.CharField()
    # cpu_req_per = serializers.CharField()
    # cpu_lmt_per = serializers.CharField()

    # mem_alloc = serializers.CharField()
    # mem_req = serializers.CharField()
    # mem_lmt = serializers.CharField()
    # mem_req_per = serializers.CharField()
    # mem_lmt_per = serializers.CharField()
