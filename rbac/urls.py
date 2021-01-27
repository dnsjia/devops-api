#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : urls.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2020/12/1
# @Desc  :
from django.urls import path, include
from rbac.views import menu, permission, role
from rest_framework.routers import SimpleRouter

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