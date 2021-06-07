#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
@Time: 2021/5/28 0028 上午 10:15
@Author: micheng. <safemonitor@outlook.com>
@File: application.py
"""

import json
import logging

from channels.generic.websocket import WebsocketConsumer, JsonWebsocketConsumer, AsyncWebsocketConsumer
from asgiref.sync import async_to_sync

from tasks import application
from tasks.application import app_diagnosis

logger = logging.getLogger('default')
consumer_list = []


class AppDiagnosisConsumer(AsyncWebsocketConsumer):
    """
    应用诊断
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agent_id = None
        self.type = None
        self.command = None
        self.room_group_name = "DEFAULT_ROOM"

    async def connect(self):
        print(self.scope)
        logger.info(f"websocket携带参数: {self.scope}")
        self.agent_id = self.scope['url_route']['kwargs']['agentId']
        self.room_group_name = self.agent_id

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        print(f'接收到的websocket数据： {text_data_json}')

        getattr(application, 'app_diagnosis').delay(self.channel_name, *text_data_json)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'arthas',
                'message': text_data_json
            }
        )

    # Receive message from room group
    async def arthas(self, event):
        print(event)

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'data': event
        }))
