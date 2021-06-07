#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
@Time: 2021/5/26 0007 下午 14:11
@Author: micheng. <safemonitor@outlook.com>
@File: test_copy.py
"""

import sys
sys.path.insert(0, "../..")

from controller.ansible.runner import AdHocRunner, CommandRunner, Options, get_default_options
from controller.ansible.inventory import BaseInventory


class TestCmd(object):
    def __init__(self):
        # self.host_data = [
        #     {
        #         "hostname": "testserver",
        #         "ip": "192.168.1.35",
        #         "port": 22,
        #         "username": "root",
        #         "password": "xxxxx.",
        #         "become": {
        #             "method": "su", # su , sudo
        #             "user": "root", # 默认以root用户执行
        #            # "pass": "123456",
        #         },
        #     },
        #     {
        #         "hostname": "Server222",
        #         "ip": "192.168.1.36",
        #         "port": 22,
        #         "username": "root",
        #         "password": "xxxxxx",
        #         "become": {
        #             "method": "su",  # su , sudo
        #             "user": "root",  # 默认以root用户执行
        #             # "pass": "123456",
        #         },
        #     },
        # ]
        self.host_data = [
            {'hostname': 'i-bp10rydhf43t7r07v8wf', 'ip': 'xxxx', 'become': {'method': 'sudo', 'user': ''},
             'username': 'mone', 'password': 'xxx', 'port': 20100},

            {
                "hostname": "testserver",
                "ip": "192.168.1.325",
                "port": 22,
                "username": "root",
                "password": "xxxx.",
                "become": {
                    "method": "su", # su , sudo
                    "user": "root", # 默认以root用户执行
                   # "pass": "123456",
                },
            },
        ]

        print(self.host_data)
        self.inventory = BaseInventory(self.host_data)
        self.runner = AdHocRunner(self.inventory)

    def test_run(self):
        # 异步任务 需要传递 task_time 任务所执行的时间， anync = 前端的task_time 180
        # poll 0

        # 在yaml palybook 中执行异步任务
        """"
        tasks:
        - shell: sleep 10; hostname -i
          async: 10 # 异步
          poll: 0

        """
        tasks = [
            {"action": {"module": "copy", "args": {"src": "/data/my-code/pigs/ansible_upload_file_tmp/000c29cd2487.zip",
                                                   "dst": "/tmp/24e0af08-bc49-11eb-b4e5-000c29cd2487.zip"},"name": "run_whoami"}}
        ]

        ret = self.runner.run(tasks, "all", 111111133333333333333334)
        print(ret)
        # print(ret.results_summary)
        # print(ret.results_raw)

    def test_execute(self):
        inventory = BaseInventory(self.host_data)
        self.runner = CommandRunner(inventory)
        res = self.runner.execute('ls -l /tmp', 'all')
        print(res.results_command)
        print(res.results_raw)


if __name__ == "__main__":
    p = TestCmd()
    p.test_run()

    # p.test_execute()
