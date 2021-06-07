#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
# @File  : ws_auth.py
# @Author: 往事随风
# @Email: gujiwork@outlook.com
# @Date  : 2021/5/30
# @Desc  :
"""

import os
import traceback
from urllib.parse import parse_qs

from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed

from apps.account.models import User
from utils.jwt_token import parse_payload

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

# Users = get_user_model()


@database_sync_to_async
def get_user(username):
    try:
        return User.objects.get(username=username)
    except User.DoesNotExist:
        return AnonymousUser()


class QueryAuthMiddleware:
    """
    Custom middleware (insecure) that takes user IDs from the query string.
    """

    def __init__(self, app):
        # Store the ASGI application we were passed
        self.app = app

    async def __call__(self, scope, receive, send):
        # Look up user from query string (you should also do things like
        # checking if it is a valid user ID, or if scope["user"] is already
        # populated).
        token = parse_qs(scope["query_string"].decode("utf8"))["token"][0]

        # Try to authenticate the user
        try:
            # This will automatically validate the token and raise an error if token is invalid
            result = parse_payload(token)
            if not result['status']:
                raise AuthenticationFailed(result)

            username = result['data'].get('username')

            scope['user'] = await get_user(username)
        except Exception:
            print(traceback.format_exc())
            raise AuthenticationFailed('认证失败！')

            # Will return a dictionary like -
            # {
            #     "token_type": "access",
            #     "exp": 1568770772,
            #     "jti": "5c15e80d65b04c20ad34d77b6703251b",
            #     "user_id": 6
            # }
            # Get the user using ID
        return await self.app(scope, receive, send)


TokenAuthMiddlewareStack = lambda inner: QueryAuthMiddleware(AuthMiddlewareStack(inner))
