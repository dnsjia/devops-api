#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
# @File  : permissions.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2020/12/1
# @Desc  :
"""

import re
import logging

from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from django.urls import URLPattern

from utils.jwt_token import parse_payload

logger = logging.getLogger('default')


class MyPermission(BasePermission):
    """
    权限认证
    """

    def __init__(self):
        # 不需要权限的路径
        self.common_paths = ['/user/login/']

    def has_permission(self, request, view):
        current_url = request.path_info
        method = request.method
        p = re.compile(r'([a-zA-Z]|[0-9]|[.])|(/.*)')
        url = p.findall(current_url)[0][1]
        if url == '/':
            raise PermissionDenied('不能访问该路径')
        for i in self.common_paths:
            i = '^{}$'.format(i)
            flag = re.match(i, url)
            if flag:
                return True
        try:
            token = request.auth
            if token is None:
                token = request.META.get('HTTP_AUTHORIZATION', '').split()[1]
            result = parse_payload(token)
            paths = []
            permissions = result['data'].get('permissions', {})
            for key in permissions.keys():
                paths.append(key)
        except Exception:
            import traceback
            logger.error('权限认证失败: %s' % str(traceback.format_exc()))
            raise PermissionDenied('权限认证失败')

        for path in paths:
            tmp = path
            path = '^{}$'.format(path)
            flag = re.match(path, url)
            if flag:
                if method in permissions[tmp] or '*' in permissions[tmp]:
                    return True
        logger.warning('用户无权限访问url：%s' % url)
        return False


def get_all_paths(patterns, pre_fix, result):
    """
    获取项目URL
    """
    for item in patterns:
        part = item.pattern.regex.pattern.strip("^$")
        if isinstance(item, URLPattern):
            if not pre_fix.startswith('/admin'):
                result.append(pre_fix.lstrip(r'[a-zA-Z]|v[a-zA-Z]|[0-9]|[.]|(/.*)') + part)
        else:
            get_all_paths(item.url_patterns, pre_fix + part, result=result)

    return result
