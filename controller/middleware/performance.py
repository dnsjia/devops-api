#!/bin/env python3
# -*- coding: utf-8 -*-

"""
@Time: 2020/11/28 15:13
@Author: yu.jiang <safemonitor@outlook.com>
@License: Apache License
@File: performance.py

"""

import time


def performance_middleware(get_response):
    def middleware(request):
        start_time = time.time()
        response = get_response(request)
        duration = time.time() - start_time
        response["X-page-Duration-ms"] = int(duration * 1000)

        return response

    return middleware
