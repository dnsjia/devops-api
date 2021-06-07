#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
@Time: 2021/4/13 0013 下午 5:14
@Author: micheng. <safemonitor@outlook.com>
@File: server.py
"""

from django.db.models import Q
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.views import APIView

from apps.cmdb.models import Server
from apps.cmdb.serializers.server import ServerSerializer
from utils.authorization import MyAuthentication
from utils.http_response import APIResponse
from utils.permissions import MyPermission
from utils.pagination import MyPageNumberPagination


class ServerView(ListAPIView):
    """
    资产列表
    """

    authentication_classes = [MyAuthentication, ]
    permission_classes = [MyPermission, ]

    serializer_class = ServerSerializer
    pagination_class = MyPageNumberPagination

    def get_queryset(self, *args, **kwargs):

        search = self.request.query_params.get('keyword')

        qs = Server.objects.all()

        if search is not None:
            qs = qs.filter(
                Q(private_ip__icontains=search) | Q(public_ip__icontains=search) | Q(hostname__icontains=search) | Q(
                    instance_id__icontains=search))

        """Filter ECS Server."""
        return qs


class ServerDetailView(RetrieveUpdateDestroyAPIView):
    """
    资产详情
    """

    authentication_classes = [MyAuthentication, ]
    permission_classes = [MyPermission, ]

    queryset = Server.objects.all()
    serializer_class = ServerSerializer


class ServerSearchView(APIView):

    authentication_classes = [MyAuthentication, ]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        """
        服务器搜索
        """
        data = request.query_params
        search = data.get('keyword')
        query_set = Server.objects.all()

        if search is not None:
            query_set = Server.objects.filter(
                Q(private_ip__icontains=search) | Q(public_ip__icontains=search) | Q(hostname__icontains=search) | Q(
                    instance_id__icontains=search))

        paginator = MyPageNumberPagination()
        page_publish_list = paginator.paginate_queryset(query_set, self.request, view=self)
        ps = ServerSerializer(page_publish_list, many=True)
        response = paginator.get_paginated_response(ps.data)
        return APIResponse(data=response.data)


