#!/bin/env python3
# -*- coding: utf-8 -*-

"""
@Time: 2020/11/4 16:52
@Author: yu.jiang <safemonitor@outlook.com>
@License: Apache License
@File: tasks.py

"""

from __future__ import absolute_import
from celery import shared_task
from django.db.models import Q
from api.models import DeployTask, DeployStatusChart
import logging
import datetime as dt

logger = logging.getLogger('default')
today = dt.date.today()
week_ago = today - dt.timedelta(days=1)


@shared_task
def dashboard_deploy_chart_count():
    """
    部署状态结转
    :return:
    """

    try:
        logger.info("开始统计部署成功数据...")
        success_count = DeployTask.objects.filter(
            Q(created_time__gt=week_ago) | Q(status=4)).count()
        DeployStatusChart.objects.filter(
            created_time=today).update_or_create(days=today, stats='部署成功',count=success_count)
        logger.info("部署成功数据统计完毕, 准备执行部署失败统计...")

        failed_count = DeployTask.objects.filter(
            Q(created_time__gt=week_ago) | Q(status=5)).count()
        DeployStatusChart.objects.filter(
            created_time=today).update_or_create(days=today, stats='部署失败',count=failed_count)
        logger.info("所有数据已结转完成..")

    except BaseException as e:
        logger.error("仪表盘数据图表结转失败, 原因:%s" % str(e))
