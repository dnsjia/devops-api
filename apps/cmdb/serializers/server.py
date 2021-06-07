#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
@Time: 2021/4/21 0021 下午 12:27
@Author: micheng. <safemonitor@outlook.com>
@File: server.py
"""

from rest_framework import serializers

from apps.cmdb.models import Server, Disk


class ServerDiskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disk
        fields = "__all__"


class ServerSerializer(serializers.ModelSerializer):
    """服务器序列化类"""
    # 反向引入disk
    disk = ServerDiskSerializer(many=True, read_only=True)

    class Meta:
        model = Server
        fields = "__all__"

    def to_representation(self, instance):
        ret = super(ServerSerializer, self).to_representation(instance)

        # ret.update({
        #     'create_at': instance.create_at.strftime('%Y-%m-%d %H:%M:%S')
        # })

        # ret["public_ip"] = "***.**.**.***"

        host = 'https://ecs.console.aliyun.com'
        ret['web_url'] = f'{host}/#/server/{instance.instance_id}/detail?regionId={instance.region_id}'
        return ret


class ExecuteTaskServerSerializer(serializers.ModelSerializer):
    """执行任务 服务器序列化类"""

    class Meta:
        model = Server
        fields = ["instance_id", "status", "private_ip", "hostname", "os_type"]