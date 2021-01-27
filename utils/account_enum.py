#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
@Author: 风哥
@Mail: gujiwork@outlook.com
@File:account_enum.py
@Time:2020/10/23 10:07
"""
from enum import Enum, unique


@unique
class AccountEnum(Enum):
    """
    "1": "内网SVN帐号",
    "2": "内网GIT帐号",
    "3": "内网JIRA帐号",
    "4": "内网网盘帐号",
    "5": "内网日志平台",
    "6": "生产日志平台",
    "7": "生产数据库帐号"
    8: 内网vpn
    """
    INNER_SVN_ACCOUNT = 1
    INNER_GIT_ACCOUNT = 2
    INNER_JIRA_ACCOUNT = 3
    INNER_PAN_DISK_ACCOUNT = 4
    INNER_LOGS_ACCOUNT = 5
    PROD_LOGS_ACCOUNT = 6
    PROD_DB_ACCOUNT = 7
    INNER_VPN_ACCOUNT = 8
