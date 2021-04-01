#!/bin/env python3
# -*- coding: utf-8 -*-

"""
@Time: 2020/9/28 10:27
@Author: yu.jiang <safemonitor@outlook.com>
@License: Apache License
@File: project.py

"""

import json
import traceback
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from api.models import Project
from api.utils.authorization import MyAuthentication
from api.utils.permissions import MyPermission
from utils.rest_page import StandardResultsSetPagination
from utils.serializer import ProjectModelSerializers
import logging
logger = logging.getLogger('default')


class QueryProjectView(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        """
        /api/v1/project/query
        :param request:
        :param args:
        :param kwargs:
        :return:
        """

        try:
            keywords = request.GET.get('keywords', None)
            if keywords is not None:
                keywords = keywords.strip()
                query_project = Project.objects.filter(title__icontains=keywords).order_by('id')
                paginator = StandardResultsSetPagination()
                project_list = paginator.paginate_queryset(query_project, self.request, view=self)
                serializer_project_info = ProjectModelSerializers(project_list, many=True)
                project_page = paginator.get_paginated_response(serializer_project_info.data)
                return Response(project_page.data)

            query_project = Project.objects.all().order_by('id')
            paginator = StandardResultsSetPagination()
            project_list = paginator.paginate_queryset(query_project, self.request, view=self)
            serializer_project_info = ProjectModelSerializers(project_list, many=True)
            project_page = paginator.get_paginated_response(serializer_project_info.data)
            return Response(project_page.data)

        except BaseException as e:
            logger.error('系统异常 %s' % str(traceback.format_exc()), e)
            return JsonResponse(data={
                "errcode": "1006",
                "msg": "系统异常, 请刷新重试!",
                "data": "null"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR, json_dumps_params={'ensure_ascii': False})

    def post(self, request, *args, **kwargs):
        """
        根据项目名称查询
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            keywords = json.loads(request.body)['params']
            query_project = Project.objects.filter(title__icontains=keywords).order_by('id')
            paginator = StandardResultsSetPagination()
            project_list = paginator.paginate_queryset(query_project, self.request, view=self)
            serializer_project_info = ProjectModelSerializers(project_list, many=True)
            project_page = paginator.get_paginated_response(serializer_project_info.data)
            return Response(project_page.data)

        except BaseException as e:
            logger.error("系统异常, 原因: %s" % str(traceback.format_exc()))
            return JsonResponse(data={
                "errcode": "1006",
                "msg": "系统异常, 请刷新重试!",
                "data": e
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR, json_dumps_params={'ensure_ascii': False})
