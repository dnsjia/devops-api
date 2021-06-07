#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
# @File  : namespace.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2020/12/7
# @Desc  :
"""

import traceback
import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from kubernetes import client, config

from utils.authorization import MyAuthentication
from utils.permissions import MyPermission

logger = logging.getLogger('default')
config.load_kube_config()
v1 = client.CoreV1Api()


class NamespaceView(APIView):

    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    """
    命名空间
    """

    def get(self, request, *args, **kwargs):
        context = {'errcode': 0, 'msg': '获取成功', 'data': ''}
        try:
            ret = v1.list_namespace()
            tmp_context = []
            for i in ret.items:
                tmp_dict = dict()
                tmp_dict['name'] = i.metadata.name
                tmp_dict['status'] = i.status.phase
                tmp_context.append(tmp_dict)
            context['data'] = tmp_context
        except Exception as e:
            logger.error('获取namespace失败：%s' % str(traceback.format_exc()), e)
            context['msg'] = '获取失败'
            context['errcode'] = 1000

        return Response(context)

    def post(self, request, *args, **kwargs):
        namespace = request.data.get('namespace')
        context = {'errcode': 0, 'msg': '创建成功'}
        try:
            body = client.V1Namespace(api_version='v1', kind='Namespace', metadata={'name': namespace})
            ret = v1.create_namespace(body=body)
            if ret.status.phase == 'Active':
                return Response(context)
        except Exception as e:
            logger.error('创建namespace失败：%s' % str(traceback.format_exc()), e)
            context['errcode'] = 1000
            context['msg'] = '创建失败'
        return Response(context)

    def delete(self, request, *args, **kwargs):
        query_params = request.query_params.dict()
        namespace = query_params.get('namespace')
        context = {'errcode': 0, 'msg': '删除成功'}
        try:
            v1.delete_namespace(name=namespace)
        except Exception as e:
            logger.error('删除namespace失败：%s' % str(traceback.format_exc()), e)
            context['errcode'] = 1000
            context['msg'] = '删除失败'
        return Response(context)
