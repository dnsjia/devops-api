#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
@Time: 2021/4/13 0013 下午 5:14
@Author: micheng. <safemonitor@outlook.com>
@File: urls.py
"""

from django.conf.urls import url
# from django.urls import path

from apps.cmdb.views.ansible_tasks import ExecuteTaskView, ExecuteTaskServerList, SearchHostView, TasksExecList, \
    UploadFile, SendFileView, SendFileList, AnsibleTemplateView, AnsibleTemplateReadView, TemplateSearch, \
    SendFileSearch, CommandSearch
from apps.cmdb.views.deploy_chart import DashboardChart

from apps.cmdb.views.domain import DomainView
from apps.cmdb.views.server import ServerView, ServerDetailView, ServerSearchView

urlpatterns = [
    url(r'^(?P<version>[v1|v2]+)/server$', ServerView.as_view(), name='ecs'),
    url(r'^(?P<version>[v1|v2]+)/server/search$', ServerSearchView.as_view()),
    url(r'^(?P<version>[v1|v2]+)/server/(?P<pk>\w+.*)$', ServerDetailView.as_view()),
    url(r'^(?P<version>[v1|v2]+)/domain$', DomainView.as_view(), name='domain'),
    # ansible task
    url(r'^(?P<version>[v1|v2]+)/ansible/server$', ExecuteTaskServerList.as_view(), name='task_server'),
    url(r'^(?P<version>[v1|v2]+)/ansible/tasks/list$', TasksExecList.as_view(), name='tasks_list'),
    url(r'^(?P<version>[v1|v2]+)/ansible/execute$', ExecuteTaskView.as_view(), name='execute_task'),
    url(r'^(?P<version>[v1|v2]+)/ansible/execute/search$', CommandSearch.as_view(), name='command_search'),
    url(r'^(?P<version>[v1|v2]+)/ansible/searchHost$', SearchHostView.as_view(), name='search_server'),
    url(r'^(?P<version>[v1|v2]+)/ansible/sendfile$', SendFileView.as_view(), name='send_file'),
    url(r'^(?P<version>[v1|v2]+)/ansible/send_list$', SendFileList.as_view(), name='send_list'),
    url(r'^(?P<version>[v1|v2]+)/ansible/sendfile/search$', SendFileSearch.as_view(), name='send_file_search'),
    url(r'^(?P<version>[v1|v2]+)/ansible/template/list$', AnsibleTemplateView.as_view(), name='template_list'),
    url(r'^(?P<version>[v1|v2]+)/ansible/template/read$', AnsibleTemplateReadView.as_view(), name='template_read'),
    url(r'^(?P<version>[v1|v2]+)/ansible/template/search$', TemplateSearch.as_view(), name='template_search'),
    url(r'^(?P<version>[v1|v2]+)/uploads$', UploadFile.as_view(), name='upload_file'),
    # 仪表盘图表
    url(r'^(?P<version>[v1|v2]+)/dashboard/count$', DashboardChart.as_view(), name='dashboard_count'),
    # url(r'^(?P<version>[v1|v2]+)/dashboard/deployChart$', DeployChart.as_view(), name='deploy_chart'),


]
