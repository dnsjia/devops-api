#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
# @File  : test_inventory.py.py
# @Author: 往事随风
# @Email: gujiwork@outlook.com
# @Date  : 2021/5/12
# @Desc  :
"""

import sys
import unittest

from controller.ansible.runner import AdHocRunner
from controller.ansible.inventory import BaseInventory

sys.path.insert(0, '../..')


class TestJMSInventory(unittest.TestCase):
    def setUp(self):
        host_list = [{
            "hostname": "testserver1",
            "ip": "192.168.1.35",
            "port": 22,
            "username": "root",
            "password": "xxxxxx.",
            "private_key": "/tmp/private_key",
            "become": {
                "method": "sudo",
                "user": "root",
                "pass": None,
            },
            "groups": ["group1", "group2"],
            "vars": {"sexy": "yes"},
        }, {
            "hostname": "testserver2",
            "ip": "192.168.1.36",
            "port": 27123,
            "username": "root",
            "password": "xxxxxx...",
            "private_key": "/tmp/private_key",
            "become": {
                "method": "su",
                "user": "root",
                "pass": "123",
            },
            "groups": ["group3", "group4"],
            "vars": {"love": "yes"},
        }]

        self.inventory = BaseInventory(host_list=host_list)
        self.runner = AdHocRunner(self.inventory)

    def test_hosts(self):
        print("#"*10 + "Hosts" + "#"*10)
        for host in self.inventory.hosts:
            print(host)

    def test_groups(self):
        print("#" * 10 + "Groups" + "#" * 10)
        for group in self.inventory.groups:
            print(group)

    def test_group_all(self):
        print("#" * 10 + "all group hosts" + "#" * 10)
        group = self.inventory.get_group('all')
        print(group.hosts)


if __name__ == '__main__':
    unittest.main()