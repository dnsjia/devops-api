#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
# @File  : urls.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2020/12/7
# @Desc  :
"""

from django.conf.urls import url
from django.urls import path

from apps.k8s.views.deployment import DeploymentViews, DetailDeploymentViews, DeploymentHistoryVersionViews
from apps.k8s.views.logs import LogsView
from apps.k8s.views.namespace import NamespaceView
from apps.k8s.views.node import NodeView, DarinNodeAndPod, NodeDetailView, NodeEventsView, NodeMetrics
from apps.k8s.views.pod import PodFromNodeView, DetailPodView, PodViews
from apps.k8s.views.events import EventsView, DeploymentEventsView
from apps.k8s.views.scale import DeploymentScaleViews

app_name = 'k8s'

urlpatterns = [
    url(r'^(?P<version>[v1|v2]+)/drain/nodes$', DarinNodeAndPod.as_view(), name='node_drain'),
    url(r'^(?P<version>[v1|v2]+)/nodes$', NodeView.as_view(), name='nodes'),
    url(r'^(?P<version>[v1|v2]+)/detail/node$', NodeDetailView.as_view(), name='detail_node'),
    url(r'^(?P<version>[v1|v2]+)/events/node$', NodeEventsView.as_view(), name='event_node'),
    url(r'^(?P<version>[v1|v2]+)/event/deployment$', DeploymentEventsView.as_view(), name='event_node'),
    url(r'^(?P<version>[v1|v2]+)/metrics/node$', NodeMetrics.as_view(), name='metrics_node'),
    url(r'^(?P<version>[v1|v2]+)/pods/node$', PodFromNodeView.as_view(), name='pod_to_node'),
    url(r'^(?P<version>[v1|v2]+)/pods/list$', PodViews.as_view(), name='pods'),
    url(r'^(?P<version>[v1|v2]+)/event/pod$', EventsView.as_view(), name='event_pod'),
    url(r'^(?P<version>[v1|v2]+)/namespaces$', NamespaceView.as_view(), name='namespaces'),
    url(r'^(?P<version>[v1|v2]+)/pod$', DetailPodView.as_view(), name='pod'),
    url(r'^(?P<version>[v1|v2]+)/logs$', LogsView.as_view(), name='logs'),
    url(r'^(?P<version>[v1|v2]+)/deployments$', DeploymentViews.as_view(), name='deployments'),
    url(r'^(?P<version>[v1|v2]+)/deployment/detail$', DetailDeploymentViews.as_view(), name='deployment'),
    url(r'^(?P<version>[v1|v2]+)/deployment/scale$', DeploymentScaleViews.as_view(), name='scale'),
    url(r'^(?P<version>[v1|v2]+)/deployment/history$', DeploymentHistoryVersionViews.as_view(), name='history_version'),
]