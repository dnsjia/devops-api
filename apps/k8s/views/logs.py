#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
# @File  : logs.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2021/2/4
# @Desc  :
"""

import traceback
import logging

from kubernetes.client import ApiException
from rest_framework.response import Response
from rest_framework.views import APIView
from kubernetes import client

from apps.account.models import User
from utils.authorization import MyAuthentication
from utils.http_response import APIResponse
from utils.permissions import MyPermission

logger = logging.getLogger('default')


class LogsView(APIView):

    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def post(self, request, *args, **kwargs):
        """
        获取pod日志信息
        """
        rsp = request.data
        pod = rsp['pod']
        namespace = rsp['namespace']
        tail_line = rsp.get('tail_line', 100)
        user_obj = User.objects.filter(username=request.user.username).first()
        user_group = user_obj.roles.all()

        if not request.user.is_superuser:

            if user_group:
                group = str(user_group[0]).strip()
                if group == 'develop' and namespace != 'develop' or namespace != 'dingtalk':
                    return APIResponse(errcode=403, errmsg='无权限查看日志', data={'data': '无权限查看日志,请联系运维处理！'})
                elif group == 'test' and namespace != 'release' or namespace != 'dingtalk':
                    return APIResponse(errcode=403, errmsg='无权限查看日志', data={'data': '无权限查看日志,请联系运维处理！'})
                else:
                    return APIResponse(errcode=403, errmsg='无权限查看日志', data={'data': '无权限查看日志,请联系运维处理！'})
            else:
                return APIResponse(errcode=403, errmsg='无权限查看日志', data={'data': '无权限查看日志,请联系运维处理！'})

        logger.info('用户：%s, 请求查看pod日志: %s, 命名空间：%s' % (str(request.user.username), pod, namespace))

        v1 = client.CoreV1Api()
        try:
            data = v1.read_namespaced_pod_log(
                name=pod, namespace=namespace, tail_lines=tail_line, follow=False, pretty=True
            )
            print(data)
            return APIResponse(data=data.split('\n'))
        except ApiException as e:
            logger.warning("获取pod日志出错, 详细信息：%s" % str(traceback.format_exc()))
            return APIResponse(errcode=9999, errmsg='获取日志异常,请联系运维处理！',  data={'data': '获取日志异常,请联系运维处理！'})