#!/bin/env python3
# -*- coding: utf-8 -*-

"""
@Time: 2020/11/3 13:02
@Author: yu.jiang <safemonitor@outlook.com>
@License: Apache License
@File: deploy_chart.py

"""
import traceback
from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from api.models import Project, Ticket, VirtualHost, DeployTask, DeployStatusChart
#from utils.jwt_middleware import TokenAuth
from api.utils.authorization import MyAuthentication
from api.utils.permissions import MyPermission
from utils.serializer import DeployStatusChartModelSerializers
import datetime as dt
import logging
logger = logging.getLogger('default')


class DashboardChart(APIView):
    # authentication_classes = [JSONWebTokenAuthentication, TokenAuth]
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission]

    def get(self, request, *args, **kwargs):
        """
        统计应用、主机、工单、部署单数量
        :param request:
        :param args:
        :param kwargs:
        :return:
        """

        try:
            application_count = Project.objects.all().count()
            ticket_count = Ticket.objects.all().count()
            virtual_host_count = VirtualHost.objects.all().count()
            deploy_count = DeployTask.objects.all().count()
            count_data = {
                "application": application_count,
                "ticket": ticket_count,
                "virtual_host": virtual_host_count,
                "deploy": deploy_count,
            }
            return JsonResponse(data={"errcode": 0, "msg": "success", "data": count_data})

        except BaseException as e:
            logger.error('获取仪表盘统计数据失败, 异常原因: %s' % str(traceback.format_exc()), e)
            return JsonResponse(data={"errcode": 5003, "msg": "获取数据失败", "data": "null"})


class DeployChart(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        """
        一周部署图表详情
        :param request:
        :param args:
        :param kwargs:
        :return:
        """

        # 配置定时任务, 每隔4小时扫描一次DeployTask表、将数据插入DeployStatusChart表中
        try:
            today = dt.date.today()
            week_ago = today - dt.timedelta(days=6) # days=6,  7会获取八天的数据
            query = DeployStatusChart.objects.filter(days__gte=week_ago)
            ser = DeployStatusChartModelSerializers(instance=query, many=True, context={'request': request})
            return JsonResponse(data={
                "errcode": 0,
                "msg": "success",
                "data": {"data": ser.data}
            }, json_dumps_params={'ensure_ascii': False})

        except BaseException as e:
            logger.error('获取仪表盘一周部署统计数据失败, 异常原因: %s' % str(traceback.format_exc()), e)

            return JsonResponse(data={
                "errcode": 5006,
                "msg": "系统异常, 获取部署状态失败！",
                "data": "null"
            }, json_dumps_params={'ensure_ascii': False})