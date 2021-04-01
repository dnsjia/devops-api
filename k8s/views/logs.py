#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : logs.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2021/2/4
# @Desc  :
import traceback
from kubernetes.client import ApiException
from rest_framework.response import Response
from rest_framework.views import APIView
from kubernetes import client
from api.utils.authorization import MyAuthentication
from api.utils.permissions import MyPermission
import logging

logger = logging.getLogger('default')


class LogsView(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def post(self, request: {}) -> Response:
        """
        获取pod日志信息
        """
        rsp = request.data['params']
        pod = rsp['pod']
        namespace = rsp['namespace']
        tail_line = rsp.get('tail_line', 100)

        v1 = client.CoreV1Api()
        try:
            data = v1.read_namespaced_pod_log(
                name=pod, namespace=namespace, tail_lines=tail_line, follow=False, pretty=True
            )
            return Response(data={'errcode': 0, 'data': data.split("\n"), 'msg': '获取日志成功'})
        except ApiException as e:
            logger.warning("获取pod日志出错, 详细信息：%s" % str(traceback.format_exc()))
            return Response(data={'errcode': 9999, 'data': ['获取日志异常,请联系运维处理！'], 'msg': '获取日志异常'})