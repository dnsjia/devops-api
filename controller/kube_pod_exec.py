#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.

"""
# @File  : kube_pod_exec.py
# @Author: 往事随风
# @Email: gujiwork@outlook.com
# @Date  : 2021/4/30
# @Desc  :
"""

import json
import logging

from kubernetes import client, config
from kubernetes.stream import stream
from kubernetes.client import ApiException

logger = logging.getLogger('default')


class KubeApi:
    def __init__(self, pod, namespace='default'):
        config.load_kube_config()
        self.namespace = namespace
        self.pod = pod

    def pod_exec(self, cols, rows):
        api_instance = client.CoreV1Api()

        exec_command = [
            "/bin/sh",
            "-c",
            'export LINES=20; export COLUMNS=100; '
            'TERM=xterm-256color; export TERM; [ -x /bin/bash ] '
            '&& ([ -x /usr/bin/script ] '
            '&& /usr/bin/script -q -c "/bin/bash" /dev/null || exec /bin/bash) '
            '|| exec /bin/sh']
        container = ""
        conf_stream = stream(api_instance.connect_get_namespaced_pod_exec,
                             name=self.pod,
                             namespace=self.namespace,
                             container=container,
                             command=exec_command,
                             stderr=True, stdin=True,
                             stdout=True, tty=True,
                             _preload_content=False
                             )

        conf_stream.write_channel(4, json.dumps({"Height": int(rows), "Width": int(cols)}))

        return conf_stream
