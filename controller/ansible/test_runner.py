#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
# @File  : test_runner.py.py
# @Author: 往事随风
# @Email: gujiwork@outlook.com
# @Date  : 2021/5/12
# @Desc  :
"""

import unittest
import sys

sys.path.insert(0, "../..")

from controller.ansible.runner import AdHocRunner, CommandRunner
from controller.ansible.inventory import BaseInventory


class TestAdHocRunner(unittest.TestCase):
    def setUp(self):
        host_data = [
            {
                "hostname": "testserver",
                "ip": "192.168.1.35",
                "port": 22,
                "username": "root",
                "password": "xxxxxx.",
            },
        ]
        inventory = BaseInventory(host_data)
        self.runner = AdHocRunner(inventory)

    def test_run(self):
        tasks = [
            {"action": {"module": "shell", "args": "ls"}, "name": "run_cmd"},
            {"action": {"module": "shell", "args": "whoami"}, "name": "run_whoami"},
        ]
        ret = self.runner.run(tasks, "all")
        print(ret.results_summary)
        print(ret.results_raw)


# class TestCommandRunner(unittest.TestCase):
#     def setUp(self):
#         host_data = [
#             {
#                 "hostname": "testserver",
#                 "ip": "192.168.1.35",
#                 "port": 22,
#                 "username": "root",
#                 "password": "xxxxx.",
#             },
#         ]
#         inventory = BaseInventory(host_data)
#         self.runner = CommandRunner(inventory)
#
#     def test_execute(self):
#         res = self.runner.execute('ls', 'all')
#         print(res.results_command)
#         print(res.results_raw)


if __name__ == "__main__":
    unittest.main()