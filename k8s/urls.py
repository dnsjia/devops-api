#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : urls.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2020/12/7
# @Desc  :
from django.urls import path
from k8s.views.logs import LogsView
from k8s.views.deployment import DeploymentViews, DetailDeploymentViews
from k8s.views.pod import PodViews, DetailPodView
from k8s.views.node import NodeVies
from k8s.views.namespace import NamespaceView

app_name = 'k8s'

urlpatterns = [
    path('nodes/', NodeVies.as_view(), name='nodes'),
    path('namespaces/', NamespaceView.as_view(), name='namespaces'),
    path('pods/', PodViews.as_view(), name='pods'),
    path('pod', DetailPodView.as_view(), name='pod'),
    path('logs', LogsView.as_view(), name='logs'),
    path('deployments/', DeploymentViews.as_view(), name='deployments'),
    path('deployment', DetailDeploymentViews.as_view(), name='deployment'),
]