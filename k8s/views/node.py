#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : node.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2020/12/7
# @Desc  :
from rest_framework.views import APIView
from rest_framework.response import Response
from kubernetes import client, config
import traceback
from api.utils.authorization import MyAuthentication
from api.utils.pagination import MyPageNumberPagination
from api.utils.permissions import MyPermission
import logging
logger = logging.getLogger('default')
config.load_kube_config()
v1 = client.CoreV1Api()


class NodeVies(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    """
    节点
    """

    def get(self, request, *args, **kwargs):
        context = {'errcode': 0, 'msg': '获取节点成功!', 'data': ''}
        try:
            ret = v1.list_node()
            tmp_context = []
            for i in ret.items:
                tmp_dict = dict()
                tmp_dict['host'] = i.status.addresses[0].address
                tmp_dict['hostname'] = i.status.addresses[1].address
                tmp_dict['labels'] = i.metadata.namespace
                tmp_dict['capacity'] = i.status.capacity
                tmp_dict['allocatable'] = i.status.allocatable
                tmp_dict['status'] = i.status.conditions[-1].status
                tmp_context.append(tmp_dict)
            paginator = MyPageNumberPagination()
            page_publish_list = paginator.paginate_queryset(tmp_context, self.request, view=self)
            context['data'] = page_publish_list
        except Exception as e:
            logger.error('获取节点信息失败：%s' % str(traceback.format_exc()))
            context['msg'] = '获取失败'
            context['errcode'] = 1000
        return Response(context)