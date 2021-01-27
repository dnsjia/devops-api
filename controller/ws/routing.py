#!/bin/env python3
#-*- coding: utf-8 -*-

"""
@Time: 2020/5/8 13:30
@Author: yu.jiang   <safemonitor@outlook.com>
@File: routing.py
"""

from channels.routing import ProtocolTypeRouter, URLRouter
from django.conf.urls import url
from consumers import tail_logs

application = ProtocolTypeRouter(
    {
        'websocket': URLRouter(
            [
                url(r'^ws$', tail_logs.TailLogsConsumer),
            ]
        )
    }
)