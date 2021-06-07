#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.

"""
ASGI config for pigs-devops-apps project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/asgi/
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.conf.urls import url
from django.core.asgi import get_asgi_application
from django.urls import re_path, path

from consumer.webssh import SSHConsumer
from consumer.ecs_webssh import EcsSSHConsumer
from consumer.application import AppDiagnosisConsumer
from utils.ws_auth import QueryAuthMiddleware, TokenAuthMiddlewareStack


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'devops_api.settings')
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pigs-devops-apps.settings')
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    # Just HTTP for now. (We can add other protocols later.)

    'websocket': TokenAuthMiddlewareStack(
        URLRouter([
            url(r'^ws/pod/(?P<ns>\w+.*)/(?P<pod_name>\w+.*)/(?P<cols>\d+.*)/(?P<rows>\d+.*)', SSHConsumer.as_asgi()),
            url(r'^ws/ecs/webssh/(?P<ecs_id>\w+.*)/(?P<cols>\d+.*)/(?P<rows>\d+.*)', EcsSSHConsumer.as_asgi()),
            url(r'^ws/application/diagnosis/(?P<agentId>\w+.*)$', AppDiagnosisConsumer.as_asgi()),
        ])
    )

})
# application = get_asgi_application()
