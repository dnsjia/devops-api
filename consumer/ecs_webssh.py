#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
# @File  : ecs_webssh.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2021/5/11
# @Desc  :
"""

import json
from threading import Thread

import paramiko
from paramiko.client import SSHClient, AutoAddPolicy
from paramiko.config import SSH_PORT
from paramiko.rsakey import RSAKey
from paramiko.ssh_exception import AuthenticationException
from io import StringIO
from channels.generic.websocket import WebsocketConsumer

from apps.account.models import User
from apps.cmdb.models import Server
from apps.cmdb.models import EcsAuthSSH


class SSH(object):
    def __init__(self, hostname, port=SSH_PORT, username='root', pkey=None, password=None, connect_timeout=10):
        if pkey is None and password is None:
            raise Exception('public key and password must have one is not None')
        self.client = None
        self.arguments = {
            'hostname': hostname,
            'port': port,
            'username': username,
            'password': password,
            'pkey': RSAKey.from_private_key(StringIO(pkey)) if isinstance(pkey, str) else pkey,
            'timeout': connect_timeout,
        }

    def get_client(self):
        if self.client is not None:
            return self.client
        self.client = SSHClient()
        self.client.set_missing_host_key_policy(AutoAddPolicy)
        self.client.connect(**self.arguments)
        return self.client

    def __enter__(self):
        if self.client is not None:
            raise RuntimeError('Already connected')
        return self.get_client()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
        self.client = None


class EcsSSHConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.user = self.scope['user']
        # print(self.scope)
        self.id = None
        # self.id = self.scope['url_route']['kwargs']['ecs_id']
        self.chan = None
        self.ssh = None
        self.width = None
        self.height = None

    def loop_read(self):
        while True:
            data = self.chan.recv(32 * 1024)
            print('read: {!r}'.format(data))
            if not data:
                self.close(3333)
                break
            self.send(text_data=data.decode())

    def receive(self, text_data=None, bytes_data=None):
        data = text_data or bytes_data
        if data:
            data = json.loads(data)
            print('write: {!r}'.format(data))
            resize = data.get('resize')
            if resize and len(resize) == 2:
                self.chan.resize_pty(*resize)
            else:
                self.chan.send(data['data'])

    def disconnect(self, code):
        self.ssh.close()
        self.chan.close()
        print('Connection close')

    def connect(self):
        print('connect ing', self.scope)
        self.id = self.scope['url_route']['kwargs'].get('ecs_id')
        self.width = int(self.scope['url_route']['kwargs'].get('cols'))
        self.height = int(self.scope['url_route']['kwargs'].get('rows'))
        self.accept()
        self.send(text_data='Connecting ...\r\n')
        name = self.scope['user']
        user_obj = User.objects.filter(name=name).first()
        user_group = user_obj.roles.all()
        print("用户: %s, 所属权限组：%s, 连接了ecs资产: %s" % (str(user_group[0]).strip(), str(user_group[0]).strip(), str(self.id)))
        if user_group:
            group = str(user_group[0]).strip()
            if group == 'ops' and user_obj.is_superuser:
                pass
            else:
                self.check_permissions()
        else:
            self.check_permissions()

        self._init()

    def _init(self):
        host = Server.objects.filter(pk=self.id).first()
        if not host:
            self.send(text_data='Unknown host\r\n')
            self.close()
        try:

            ssh_obj = EcsAuthSSH.objects.filter(server_type='linux').first()
            # raise Exception('私钥或者密码必须有一个不为空')
            print('连接的服务器id：', self.id)

            print(ssh_obj.type)
            if ssh_obj is not None:
                if ssh_obj.type == 'password' and self.id:
                    ssh = SSH(hostname=host.private_ip, port=ssh_obj.port, username=ssh_obj.username,
                              password=ssh_obj.password, )
                elif ssh_obj.type == 'key' and self.id:
                    ssh = SSH(hostname=host.private_ip, port=ssh_obj.port, username=ssh_obj.username,
                              pkey=ssh_obj.key, )
            else:
                self.close()
                return '没有配置认证方式'

            self.ssh = ssh.get_client()
            self.chan = self.ssh.invoke_shell(term='xterm')
            self.chan.transport.set_keepalive(30)
            Thread(target=self.loop_read).start()
        except Exception as e:
            print('连接出现异常', e)
            self.send(text_data=f'主机连接失败: {e}\r\n')
            self.close()
            return

    def check_permissions(self):
        self.send(text_data='无权限访问, 请联系运维人员！\n')
        self.close()
        return False
