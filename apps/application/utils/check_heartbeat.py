#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
@Time: 2021/5/27 0027 下午 12:18
@Author: micheng. <safemonitor@outlook.com>
@File: check_heartbeat.py
"""

import logging
import os
import time

import paramiko
import requests
from paramiko.ssh_exception import NoValidConnectionsError, AuthenticationException

from devops_api.settings import BASE_DIR

logger = logging.getLogger('default')


class SendHeartBeat(object):

    @staticmethod
    def check_agent(ip: str) -> bool:
        """
        :params ip 应用主机IP地址
        """
        count = 0
        while True:
            count += 1
            try:
                check = requests.get(url='http://{}:8563/api'.format(ip), timeout=5)
                time.sleep(1)
                if check.status_code == 200:
                    logger.info(f'agent存活状态检查, host: {ip} up: Running count: {count}')
                    if count == 3:
                        return True

            except BaseException as e:
                print(e)
                logger.error(f'agent客户端已离线, host: {ip}, up: Shutdown')
                return False

    @staticmethod
    def install_agent(name: str, ip: str) -> bool:
        """
        :params name 应用名称
        :params ip 应用所在主机ip
        """

        # todo ssh安装agent, 安装完成后，将session_id, consumer_id写入redis, 同时数据激活字段设置为1
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # ssh 证书路径
        private_key = paramiko.RSAKey.from_private_key_file(os.path.join(BASE_DIR, 'utils', 'sshKey'))
        try:
            client.connect(hostname=ip,
                           port=20199,
                           username='ecs-user',
                           pkey=private_key
                           )
            cmd = """java -jar /opt/arthas-boot.jar 
            --attach-only
            --target-ip '%s'  
            --agent-id '%s' `ps aux|grep -v grep |grep math |awk '{print $2}'`
            """ % (name, ip)
            stdin, stdout, stderr = client.exec_command(cmd)

        except NoValidConnectionsError as e:
            print('远程主机建立连接失败', e)
            logger.error(f'远程主机建立连接失败, 主机地址: {ip}')
            return False

        except AuthenticationException as e:
            print("密码错误", e)
            logger.error('由于密码错误， 远程主机建立连接失败！')
            return False

        else:
            if stderr.readlines():
                logger.error('agent安装失败: %s' % stderr.read().decode('utf-8'))
                return False

            logger.info(f'{name} agent安装成功...')
            return True

        finally:
            client.close()
