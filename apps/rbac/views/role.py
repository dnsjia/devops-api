#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
@Time: 2020/12/1 0026 上午 11:29
@Author: micheng. <safemonitor@outlook.com>
@File: role.py
"""

from rest_framework.viewsets import ModelViewSet

from apps.rbac.models import Role
from apps.rbac.serializers import roles_serializers
from utils.http_response import APIResponse
from utils.tree import tree_filter


class RoleView(ModelViewSet):
    """
    角色管理
    """
    queryset = Role.objects.all()
    serializer_class = roles_serializers.RoleListSerializer

    def create(self, request, *args, **kwargs):
        data = request.data
        role_obj = Role.objects.filter(name=data['name']).first()
        if role_obj is not None and role_obj.name == data['name']:
            return APIResponse(errcode=400, errmsg='角色已存在')
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return APIResponse(data={'msg': '角色新增成功'})

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return APIResponse(data={'msg': '角色修改成功'})

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return APIResponse(data={'msg': '角色删除成功'})

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'retrieve':
            return roles_serializers.RoleListSerializer

        return roles_serializers.RoleModifySerializer

    def list(self, request, *args, **kwargs):
        """
        树型化权限和菜单
        """
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            for item in serializer.data:
                permissions = tree_filter(item['permissions'])
                menus = tree_filter(item['menus'])
                item['permissions'] = permissions
                item['menus'] = menus
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        for item in serializer.data:
            permissions = tree_filter(item['permissions'])
            menus = tree_filter(item['menus'])
            item['permissions'] = permissions
            item['menus'] = menus
        return APIResponse(data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """
        树型化权限和菜单
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        permissions = tree_filter(serializer.data['permissions'])
        menus = tree_filter(serializer.data['menus'])
        serializer.data['permissions'] = permissions
        serializer.data['menus'] = menus
        return APIResponse(data=serializer.data)

