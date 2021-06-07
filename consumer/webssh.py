#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
# @File  : webssh.py
# @Author: 往事随风
# @Email: gujiwork@outlook.com
# @Date  : 2021/4/30
# @Desc  :
"""

import logging
import time
from threading import Thread
from threading import Event

from channels.exceptions import StopConsumer
from channels.generic.websocket import WebsocketConsumer

from apps.account.models import User
from controller.kube_pod_exec import KubeApi

logger = logging.getLogger('default')


class K8SStreamThread(Thread):
    def __init__(self, websocket, container_stream):
        Thread.__init__(self)
        self.websocket = websocket
        self.stream = container_stream
        self._stop_event = Event()

    def stop(self):
        self._stop_event.set()

    def run(self):
        while self.stream.is_open():
            time.sleep(0.1)
            if not self.stream.is_open():
                self.websocket.close()
            try:
                if self.stream.peek_stdout():
                    stdout = self.stream.read_stdout()
                    self.websocket.send(stdout)
                if self.stream.peek_stderr():
                    stderr = self.stream.read_stderr()
                    self.websocket.send(stderr)
            except Exception as err:
                self.stream.write_stdin('exit\r')
                self.stream.close()
                self.websocket.close()

        else:
            # self.websocket.send('\n由于长时间没有操作，连接已断开!', close=True)
            # self.stream.write_stdin('exit\r')
            self.stream.close()
            self.stop()
            self.websocket.close()
            # print("websocket连接关闭了哦")
            # print("stream连接关闭了哦")
            # self.websocket.close()


class SSHConsumer(WebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.namespace = ''
        self.name = ''
        self.cols = ''
        self.rows = ''
        self.stream = None
        self.kube_stream = None

    def connect(self):
        logger.info(self.scope["url_route"])
        self.namespace = self.scope["url_route"]["kwargs"]["ns"]
        self.name = self.scope["url_route"]["kwargs"]["pod_name"]
        self.cols = self.scope["url_route"]["kwargs"]["cols"]
        self.rows = self.scope["url_route"]["kwargs"]["rows"]
        self.stream = KubeApi(self.name, self.namespace).pod_exec(self.cols, self.rows)
        # kube exec
        self.kub_stream = K8SStreamThread(self, self.stream)
        self.kub_stream.setDaemon(True)
        self.kub_stream.start()
        self.accept()

        name = self.scope['user']
        user_obj = User.objects.filter(name=name).first()
        user_group = user_obj.roles.all()
        if user_group:
            group = str(user_group[0]).strip()
            if group == 'test' and self.namespace not in ['release', 'dingtalk']:
                self.check_permissions()
            elif group == 'develop' and self.namespace not in ['develop', 'dingtalk']:
                self.check_permissions()
            else:
                pass
        else:
            self.check_permissions()

    def disconnect(self, close_code):
        try:
            self.stream.write_stdin('exit\r')
            self.stream.close()
            self.close()
        finally:
            self.kub_stream.stop()
            raise StopConsumer()

    def receive(self, text_data=None, bytes_data=None):
        try:
            self.stream.write_stdin(text_data)
        except Exception:
            self.stream.write_stdin('exit\r')
            self.stream.close()
            self.kub_stream.stop()
            self.close()

    def check_permissions(self):
        self.send(text_data='您无权限访问, 请联系运维人员！\n')
        self.stream.close()
        self.kub_stream.stop()
        self.close()
        return False

    def websocket_disconnect(self, message):
        """
        客户端主动断开了连接
        :param message:
        :return:
        """
        self.stream.close()
        self.kub_stream.stop()
        self.close()
        raise StopConsumer()

