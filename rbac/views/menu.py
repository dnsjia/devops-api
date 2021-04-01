#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : menu.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2020/12/1
# @Desc  :
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from api.utils.authorization import MyAuthentication
from api.utils.permissions import MyPermission
from rbac.models import Menu
from rbac.serializers import menu_serializers
from api.utils.pagination import MenuPagination
from api.utils.tree import tree_filter
from api.models import UserInfo
import logging
import traceback
logger = logging.getLogger('default')


class MenuView(ModelViewSet):
    """
    菜单管理
    """
    pagination_class = MenuPagination
    permission_classes = []
    queryset = Menu.objects.all()
    serializer_class = menu_serializers.MenuSerializer


class MenuTreeView(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    """
    菜单树
    """

    def get(self, request, *args, **kwargs):
        try:
            username = request.user.username
        except Exception as e :
            logger.error('获取用户信息出错了:%s' % str(traceback.format_exc()), e)
            username = request.user['data']
        try:

            user_obj = UserInfo.objects.filter(username=username).first()
            menus_list = user_obj.roles.all().values('menus')
        except Exception as e:
            logger.error('无法解析菜单: %s' % e)
            return Response(status=status.HTTP_403_FORBIDDEN)
        menus = [i.get('menus') for i in menus_list]
        queryset = Menu.objects.all()
        # 序列化菜单
        serializer = menu_serializers.MenuSerializer(queryset, many=True)
        # 树形菜单
        results = tree_filter(serializer.data, menus)
        return Response(results)
