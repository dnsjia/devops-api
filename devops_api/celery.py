#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
@Time: 2021/4/14 0014 下午 12:11
@Author: micheng. <safemonitor@outlook.com>
@File: celery.py
"""

from __future__ import absolute_import, unicode_literals
import os
from datetime import timedelta

from decouple import config
from django.conf import settings
from celery import Celery, platforms
from celery.schedules import crontab


# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'devops_api.settings')
CELERY_BROKER_REDIS_PASS = config('CELERY_BROKER_REDIS_PASS')
CELERY_BROKER_REDIS_HOST = config('CELERY_BROKER_REDIS_HOST')
CELERY_BROKER_REDIS_PORT = config('CELERY_BROKER_REDIS_PORT')
CELERY_BROKER_REDIS_DB = config('CELERY_BROKER_REDIS_DB')

CELERY_BACKEND_REDIS_PASS = config('CELERY_BACKEND_REDIS_PASS')
CELERY_BACKEND_REDIS_HOST = config('CELERY_BACKEND_REDIS_HOST')
CELERY_BACKEND_REDIS_PORT = config('CELERY_BACKEND_REDIS_PORT')
CELERY_BACKEND_REDIS_DB = config('CELERY_BACKEND_REDIS_DB')

app = Celery('devops_api',
             broker=f'redis://:{CELERY_BROKER_REDIS_PASS}@{CELERY_BROKER_REDIS_HOST}:{CELERY_BROKER_REDIS_PORT}/{CELERY_BROKER_REDIS_DB}',
             backend=f'redis://:{CELERY_BACKEND_REDIS_PASS}@{CELERY_BACKEND_REDIS_HOST}:{CELERY_BACKEND_REDIS_PORT}/{CELERY_BACKEND_REDIS_DB}',
             include=['tasks.aliyun',
                      'tasks.domain',
                      'tasks.ansible_cmd',
                      'tasks.email',
                      ])

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# app.conf['imports'] = ['tasks.aliyun']
# 允许root 用户运行celery
platforms.C_FORCE_ROOT = True

app.conf.beat_schedule = {
    # Executes every Monday morning at 7:30 a.m.
    # https://docs.celeryproject.org/en/4.4.2/userguide/periodic-tasks.html
    'sync_ecs': {
        'task': 'tasks.aliyun.sync_ecs',
        'schedule': crontab(minute=0, hour='*/4'),
        # 'args': ("1"),
    },
    'sync_cloud_disk': {
        'task': 'tasks.aliyun.sync_cloud_disk',
        'schedule': crontab(minute=0, hour='*/8'),
        # 'args': ("1"),
    },
    # 'sync_domain': {
    #     'task': 'tasks.domain.sync_domain',
    #     'schedule': timedelta(seconds=1800),
    # }
}
