#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
@Time: 2021/5/26 0026 上午 11:03
@Author: micheng. <safemonitor@outlook.com>
@File: diagnosis.py
"""

import logging
import json
import time

import demjson
import requests
from requests import ConnectTimeout

from django.db import transaction
from django_redis import get_redis_connection
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView

from apps.application.serializers.app_diagnosis import DiagnosisSerializer
from apps.application.models import Diagnosis
from apps.application.utils.check_heartbeat import SendHeartBeat
from utils.authorization import MyAuthentication
from utils.permissions import MyPermission
from utils.http_response import APIResponse

logger = logging.getLogger('default')


class ArtHasInstallView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        """
        安装arthas 诊断客户端
        """

        try:
            request_data = request.data
            query = Diagnosis.objects.filter(name=request_data['agentId']).values('name', 'ip', 'is_active')
            app_name = query[0]['name']
            app_ip = query[0]['ip']

            if SendHeartBeat.check_agent(app_ip):
                logger.info(f'name: {app_name} ip: {app_ip} 心跳正常, 请勿重复安装agent！')
                return APIResponse(errcode=0, errmsg='心跳正常, 请勿重复安装agent！')

            elif SendHeartBeat.install_agent(name=app_name, ip=app_ip):
                try:
                    # todo 安装arthas客户端, 这里调用celery异步任务
                    Diagnosis.objects.filter(name=request_data['agentId']).update(is_active='1')
                    logger.info(f'诊断Agent安装成功 name: {app_name} ')
                    return APIResponse(errcode=0, errmsg='诊断Agent安装成功')
                except BaseException as e:
                    print(e)
                    logger.error(f'{app_name} {app_ip} agent安装成功, 更新数据库失败!')
            else:
                return APIResponse(errcode=5000, errmsg='系统异常, 安装诊断客户端失败')

        except BaseException as e:
            print(e)
            logger.error(f'系统异常, 安装诊断客户端失败: {e}')
            return APIResponse(errcode=5001, errmsg='系统异常, 安装诊断客户端失败')


class ArtHasView(APIView):

    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def post(self, request, *args, **kwargs):

        request_data = request.data
        try:
            query = Diagnosis.objects.filter(name=request_data['agentId']).values('name', 'ip', 'is_active')
            print(request_data, query)
            app_ip = query[0]['ip']
            url = f"http://{app_ip}:8563/api"
            headers = {
                "Content-Type": "application/json;charset=utf-8"
            }
            send_data = {
                "action": "exec",
                "command": None,
            }
            init = {"action": "init_session"}
            rsp = requests.post(url=url, data=json.dumps(init), headers=headers, timeout=5)

            if rsp.status_code == 200:
                print('请求原始数据： %s' % request_data)
                logger.info(f'请求原始数据: {request_data}')
                if request_data['command'] == 'thread':
                    # 查询所有线程 thread --all
                    send_data['command'] = "thread --all"

                elif request_data['command'] == 'dashboard -n 1':
                    # 获取dashboard 数据 dashboard -n 1
                    send_data['command'] = "dashboard -n 1"

                elif request_data['type'] == 'queryThread':
                    send_data['command'] = "%s" % request_data['command']

                elif request_data['type'] == 'queryJVM':
                    # 获取jvm数据
                    send_data['command'] = "jvm"

                elif request_data['type'] == 'queryClassSource':
                    # 通过jad命令查看class源码
                    class_name = request_data['command']['className']
                    method_name = request_data['command']['methodName']
                    send_data['command'] = "jad %s %s --lineNumber false" % (class_name, method_name)

                else:
                    return APIResponse(errcode=4003, errmsg='命令执行失败, 失败原因：该接口暂不支持!')

                result = requests.post(url=url, data=json.dumps(send_data), headers=headers)
                if result.status_code == 200:
                    data = demjson.decode(result.content)
                    logger.info(f'请求的报文: {send_data}, 返回结果: {data}')
                    return APIResponse(errcode=0, errmsg='获取线程成功', data=data)
                else:
                    return APIResponse(errcode=5004, errmsg='获取线程发生异常，请刷新后再试！')

            else:
                return APIResponse(errcode=5005, errmsg='初始化会话失败, 请刷新后再试！')
        except BaseException as e:
            print(e)
            logger.error(f'系统发生异常， 异常原因：{e}')
            return APIResponse(errcode=5006, errmsg='系统发生异常， 请刷新后再试！')


class ListServiceNameView(ListAPIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]
    serializer_class = DiagnosisSerializer

    def get_queryset(self):
        """列出应用诊断服务名."""
        return Diagnosis.objects.all()
