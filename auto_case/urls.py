#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : urls.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2021/1/10
# @Desc  :
from django.urls import path
from auto_case.views import TestCaseAdd, TestCaseList, TestDetailById, TestRunner, TestCaseTask, TestCaseTaskLogs


urlpatterns = [
    path('list/', TestCaseList.as_view()),
    path('insert/',TestCaseAdd.as_view()),
    path('<int:pk>/', TestDetailById.as_view()),
    path('runner/', TestRunner.as_view(), name='runner'),
    path('task_logs/', TestCaseTaskLogs.as_view()),
    path('task', TestCaseTask.as_view()),
]
