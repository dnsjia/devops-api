#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
@Time: 2021/5/28 0028 上午 11:18
@Author: micheng. <safemonitor@outlook.com>
@File: application.py
"""

import json
import logging
import time

import requests
from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django_redis import get_redis_connection
from apps.cmdb.models import Server
from apps.application.models import Diagnosis

channel_layer = get_channel_layer()
logger = logging.getLogger('default')


@shared_task
def app_diagnosis(channel_name, data: dict):
    """"
    :params agent_id为字典 {"type": "trace", "command": {"trace com.trip"}}
    """
    print(data, '字典data')
    agent_id = data['command']['agentId']
    queryset = Diagnosis.objects.filter(name=agent_id).values('ip')
    trace_thread = TraceThread(agent_id, queryset.ip, data)
    result = trace_thread.result()
    if result:
        logger.info(f'线程追踪完毕: {result}')
        async_to_sync(channel_layer.send)(channel_name, {"type": "arthas", "message": str(result)})
    else:
        return False


class TraceThread(object):
    def __init__(self, agent_id, ip, data):
        self.data = data
        self.agent_id = agent_id
        self.url = f"http://{ip}:8563/api"
        self.headers = {
            "Content-Type": "application/json;charset=utf-8"
        }
        self.init = {"action": "init_session"}
        self.class_name = data['command']['className']
        self.method_name = data['command']['methodName']
        self.trace_time = data['command']['traceTime']
        self.trace_count = data['command']['traceCount']
        self.trace_filter = data['command']['traceFilter']

    def _init_session(self, agent_id: str) -> list:
        self.agent_id = agent_id

        """
        :params agent_id 诊断客户端名称
        """

        # 获取session_id、 consumer_id, 如果过期重新初始化会话
        conn_redis = get_redis_connection('default')
        agent_session_key = conn_redis.get(self.agent_id)
        if agent_session_key is None:
            try:
                response = requests.post(self.url, data=json.dumps(self.init), headers=self.headers, timeout=5)
                if response.status_code == 200:
                    data = json.loads(response.content)
                    consumer_id = data['consumerId']
                    session_id = data['sessionId']
                    conn_redis.set(self.agent_id, session_id + "_" + consumer_id)
                    return [session_id, consumer_id]
                else:
                    logger.error('初始化会话失败, 请刷新后再试')
                    return []
            except BaseException as e:
                print(e)
                logger.error('session_id过期, 重新初始化会话失败!')
                return []
        else:
            return agent_session_key.split("_")

    def result(self):
        # 判断初始化session是否成功
        if not TraceThread._init_session(self, agent_id=self.agent_id):
            return False

        else:
            session_id, consumer_id = TraceThread._init_session(self, agent_id=self.agent_id)
            skip_jdk_method = '--skipJDKMethod false'
            async_data = {
                "action": "async_exec",
                "command": None,
                "sessionId": session_id
            }
            if self.trace_time and self.trace_count and self.trace_filter:
                async_data["command"] = "trace %s %s '%s' %s %s" % (self.class_name, self.method_name,
                                                                    '#cost > 5', '-n 20', skip_jdk_method)
            elif self.trace_count and self.trace_filter:
                async_data["command"] = "trace %s %s %s %s" % (self.class_name, self.method_name,
                                                               '-n 20', skip_jdk_method)

            elif self.trace_time and self.trace_filter:
                async_data["command"] = "trace %s %s '%s' %s" % (self.class_name, self.method_name,
                                                                 '#cost > 5', skip_jdk_method),

            elif self.trace_time and self.trace_count:
                async_data["command"] = "trace %s %s '%s' %s" %(self.class_name, self.method_name, '#cost > 5', '-n 20')

            elif self.trace_time:
                async_data["command"] = "trace %s %s  -n 5" % (self.class_name, self.method_name)

            elif self.trace_count:
                async_data["command"] = "trace %s %s %s" % (self.class_name, self.method_name, '-n 20')

            elif self.trace_filter:
                async_data["command"] = "trace %s %s %s" % (self.class_name, self.method_name, skip_jdk_method)

            else:
                async_data["command"] = "trace %s %s '%s'" % (self.class_name, self.method_name, '-n 50')

            print('发送的数据：%s' % async_data)
            requests.post(url=self.url, data=json.dumps(async_data), headers=self.headers, timeout=5)

            while True:
                pull_data = {
                    "action": "pull_results",
                    "sessionId": session_id,
                    "consumerId": consumer_id
                }

                rsp = requests.post(url=self.url, data=json.dumps(pull_data), headers=self.headers)
                time.sleep(1)
                try:
                    if rsp.status_code == 200:
                        data = json.loads(rsp.content)
                        return data

                except BaseException as e:
                    print(e)
                    logger.error(f'获取异步任务结果异常！{e}')
                    return False


@shared_task
def install_agent(app_name: str, ip: str):
    """
    :params app_name 应用名
    :params ip 应用ip
    """
    # 获取arthas安装包
    # 判断art心跳是否正常， 正常则不安装
    pass