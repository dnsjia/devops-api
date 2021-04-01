#!/bin/env python3
# -*- coding: utf-8 -*-

"""
@Time: 2020/5/8 13:47
@Author: yu.jiang   <safemonitor@outlook.com>
@File: tail_logs.py
"""

import asyncio
import os
import paramiko
from channels.generic.websocket import WebsocketConsumer
from channels.exceptions import StopConsumer
from api.models import BuildHistory
import logging
logger = logging.getLogger('default')

CONSUMER_OBJECT_LIST = []


class TailLogsConsumer(WebsocketConsumer):

    def websocket_connect(self, message):
        """
        客户端发来连接请求之后会被触发
        :param message:
        :return:
        """
        self.accept()
        CONSUMER_OBJECT_LIST.append(self)

    def websocket_receive(self, message):
        """
        客户端向服务端发送消息， 此方法自动触发
        :param message:
        :return:
        """

        logger.info('客户端来了', message)
        logger.info("接受来自WS客户端消息: %s" % str(message))
        data = eval(message['text'])
        task_id = data.get("task_id")
        obj = BuildHistory.objects.filter(task_id=task_id).first()
        if obj is None:
            self.send('{"errcode": "-1", "msg": "当前没有日志"}')
            return False

        build_id = obj.build_id
        project_name = obj.app_name
        command = 'sudo tail -n 100 -f /data/es-data/jenkins/jobs/%s/builds/%s/log' % (project_name, build_id)
        # 远程连接服务器
        remote_ip = 'xxxxxxxx'
        username = 'xxxxxxx'
        port = 22
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        private_key = paramiko.RSAKey.from_private_key_file(BASE_DIR + '\\api\\utils\\dev')
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=remote_ip, port=port, username=username, pkey=private_key, timeout=15)

        transport = ssh.get_transport()
        channel = transport.open_session()
        channel.get_pty()

        # 务必要加上get_pty=True,否则执行命令会没有权限
        channel.exec_command(command, )
        # stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)
        # # 循环发送消息给前端页面
        import select
        from ansi2html import Ansi2HTMLConverter
        conv = Ansi2HTMLConverter(inline=True)
        while True:
            # 判断退出的准备状态
            if channel.exit_status_ready():
                break
            try:
                rl, wl, el = select.select([channel], [], [])
                if len(rl) > 0:
                    recv = channel.recv(10240)
                    # 此处将获取的数据解码成gbk的存入本地日志
                    st = recv.decode('utf-8').split('\n')
                    for i in st:
                        # logger.info("获取日志成功")
                        self.send('{"errcode": 0, "msg": "获取日志成功", "data": "%s"}' % conv.convert(str(i).strip(), full=False))

            except KeyboardInterrupt:
                # 发送 ctrl+c
                channel.send("\x03")
                channel.close()

            except asyncio.exceptions.CancelledError:
                logger.warning("连接关闭")
                channel.send("\x03")
                channel.close()

    def websocket_disconnect(self, message):
        """
        客户端主动断开了连接
        :param message:
        :return:
        """
        print('客户端断开了')
        raise StopConsumer()
