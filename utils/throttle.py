#!/bin/env python3
# -*- coding: utf-8 -*-

"""
@Time: 2020/9/29 14:25
@Author: yu.jiang <safemonitor@outlook.com>
@License: Apache License
@File: throttle.py

"""

from rest_framework.throttling import SimpleRateThrottle


class VisitThrottle(SimpleRateThrottle):
    # key名，需要在settings.py中配置
    scope = "user"

    def get_cache_key(self, request, view):
        return self.get_ident(request)