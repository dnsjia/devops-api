#!/bin/env python3
# -*- coding: utf-8 -*-

"""
@Time: 2020/11/11 16:02
@Author: yu.jiang <safemonitor@outlook.com>
@License: Apache License
@File: csrf_disable.py

"""

from rest_framework.authentication import SessionAuthentication, BasicAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening