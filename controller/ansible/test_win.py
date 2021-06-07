#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
# @File  : test_win.py
# @Author: 往事随风
# @Email: gujiwork@outlook.com
# @Date  : 2021/5/20
# @Desc  :
"""

from rest_framework.views import APIView

from controller.ansible.inventory import BaseInventory
from controller.ansible.runner import Options, AdHocRunner
from utils.http_response import APIResponse


class AnsibleWin(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        host_data = [
            {'hostname': 'i-bp10rydhf43t7r07v8wf', 'ip': '123.56.83.237',
             'username': 'administrator', 'password': 'xxx.', 'port': 5985},
        ]

        print(host_data)
        inventory = BaseInventory(host_data)
        Options.connection = 'winrm'
        runner = AdHocRunner(inventory, options=Options)
        tasks = [
            {"action": {"module": "win_command", "args": r'powershell C:\Users\Administrator\Desktop\test.ps1'}, "name": "run_whoami"},
        ]

        ret = runner.run(tasks, "all", 111111133333333333333334)
        print(ret)
        # print(ret.results_summary)
        # print(ret.results_raw)
        return APIResponse(data=ret.results_raw)
