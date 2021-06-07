#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
# @File  : test_cmd.py
# @Author: 往事随风
# @Email: gujiwork@outlook.com
# @Date  : 2021/5/12
# @Desc  :
"""

import unittest
import sys

sys.path.insert(0, "../..")

from controller.ansible.runner import AdHocRunner, CommandRunner, PlayBookRunner, get_default_options, Options
from controller.ansible.inventory import BaseInventory


class TestCmd(object):
    def __init__(self):
        host_list = [{
            "hostname": "testserver1",
            "ip": "192.168.1.35",
            "port": 22,
            "username": "root",
            "password": "xxxxx.",
            # "private_key": "/tmp/private_key",
            # "become": {
            #     "method": "sudo",
            #     "user": "root",
            #     "pass": None,
            # },
            "groups": ["group1", "group2"],
            "vars": {"sexy": "yes"},
        }, {
            "hostname": "testserver2",
            "ip": "192.168.1.36",
            "port": 27123,
            "username": "root",
            "password": "xxxxxxx.",
            # "private_key": "/tmp/private_key",
            # "become": {
            #     "method": "su",
            #     "user": "root",
            #     "pass": "123",
            # },
            "groups": ["group3", "group4"],
            "vars": {"love": "yes"},
        }]
        print(host_list)
        self.inventory = BaseInventory(host_list=host_list)
        Options.playbook_path = '/tmp/test.yaml'
        Options.passwords = ''
        self.runner = PlayBookRunner(inventory=self.inventory, options=Options)

    def test_run(self):
        ret = self.runner.run()
        import json
        print(json.dumps(ret, indent=4))
        # print(ret.results_raw)


if __name__ == "__main__":
    p = TestCmd()
    p.test_run()
