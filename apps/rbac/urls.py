#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
# @File  : urls.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2020/12/1
# @Desc  :
"""

from django.urls import path, include
from rest_framework.routers import SimpleRouter

from apps.rbac.views import menu, permission, role

app_name = 'rbac'

router = SimpleRouter()
router.register(r'roles', role.RoleView, basename='roles')  # 权限管理
router.register(r'permissions', permission.PermissionView, basename='permissions')  # 权限管理
router.register(r'menu', menu.MenuView, basename='menu')  # 菜单管理


urlpatterns = [
    path('menu/tree/', menu.MenuTreeView.as_view()),
    path('init_permission/', permission.InitPermission.as_view()),
    path('paths/', permission.PermissionPath.as_view()),
    path('permissions/tree/', permission.PermissionTree.as_view()),
    path('permissions/all/', permission.PermissionAll.as_view()),
    path('', include(router.urls)),

]