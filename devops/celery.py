#!/bin/env python3
# -*- coding: utf-8 -*-

"""
@Time: 2020/10/12 15:57
@Author: yu.jiang <safemonitor@outlook.com>
@License: Apache License
@File: celery.py

# """
from __future__ import absolute_import, unicode_literals
import os
from datetime import timedelta


from django.utils import timezone
from devops import settings
from celery import Celery, platforms
from celery.schedules import crontab

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'devops.settings')

app = Celery('devops')

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
# 解决时区问题,定时任务启动就循环输出
app.now = timezone.now

# 允许root 用户运行celery
#platforms.C_FORCE_ROOT = True

app.conf.update(
    CELERYBEAT_SCHEDULE = {
        'dashbarod_deploy_chart_count': {
            'task': 'api.tasks.dashboard_deploy_chart_count',
            'schedule': timedelta(seconds=300),
            # 'schedule': crontab(hour='*', minute='*/30', day_of_week='*'),
        },
    }
)