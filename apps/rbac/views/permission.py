#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
@Time: 2020/12/1 0026 下午 13:03
@Author: micheng. <safemonitor@outlook.com>
@File: permission.py
"""

from django.apps import apps
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from devops_api import urls
from apps.rbac.models import Permission
from apps.rbac.serializers import permission_serializers
from utils.pagination import MaxPagination
from utils.permissions import get_all_paths, MyPermission
from utils.tree import tree_filter
from utils.authorization import MyAuthentication


class PermissionView(ModelViewSet):

    """
    权限管理
    """
    pagination_class = MaxPagination
    queryset = Permission.objects.all()
    serializer_class = permission_serializers.PermissionSerializer


class PermissionAll(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    """
    获取所有权限
    """

    def get(self, request, *args, **kwargs):
        queryset = Permission.objects.all()
        serializer = permission_serializers.PermissionSerializer(queryset, many=True)
        results = serializer.data
        return Response(results)


class PermissionTree(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    """
    权限树
    """

    def get(self, request, *args, **kwargs):
        queryset = Permission.objects.all()
        serializer = permission_serializers.PermissionSerializer(queryset, many=True)
        results = tree_filter(serializer.data)
        return Response(results)


class InitPermission(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    """
    初始化权限表
    """

    def get(self, request, *args, **kwargs):
        methods = {'GET': '查看', 'POST': '添加', 'DELETE': '删除', 'PUT': '修改'}
        model = apps.get_models()
        try:
            for i in model:
                if i._meta.app_label in ['auth', 'contenttypes', 'sessions']:
                    continue
                for method, desc in methods.items():
                    Permission.objects.update_or_create(method=method, name=str(desc) + str(i._meta.verbose_name))
        except Exception as e:
            print(e)
            content = {'msg': '初始化失败!'}
            return Response(content, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({'msg': '初始化成功!'})


class PermissionPath(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    """
    获取权限path
    """

    def get(self, request, *args, **kwargs):
        path = get_all_paths(urls.urlpatterns, pre_fix="/", result=[], )
        result = list(map(lambda x: '/' + x, path))
        return Response({'path': result})
