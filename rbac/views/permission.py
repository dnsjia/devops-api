#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : permission.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2020/12/1
# @Desc  :
from django.apps import apps
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from api.utils.authorization import MyAuthentication
from devops import urls
from rbac.models import Permission
from rbac.serializers import permission_serializers
from api.utils.pagination import MaxPagination
from api.utils.permissions import get_all_paths, MyPermission
from api.utils.tree import tree_filter


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
