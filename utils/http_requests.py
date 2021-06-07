#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
# @File  : http_requests.py
# @Author: 往事随风
# @Email: gujiwork@outlook.com
# @Date  : 2021/4/12
# @Desc  :
"""

import requests


class RequestResult:

    @staticmethod
    def get(url, params=None):
        try:
            res = requests.get(url=url, params=params)
            return res.json()

        except BaseException as e:
            data = {'errcode': -1, 'errmsg': str(e)}
            return data

    @staticmethod
    def post(url, data=None, headers=None):
        if headers is None:
            headers = {}

        try:
            res = requests.post(url=url, data=data, headers=headers)
            return res.json()

        except BaseException as e:
            data = {'errcode': -1, 'errmsg': str(e)}
            return data
