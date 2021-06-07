#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
@Time: 2021/5/26 0026 上午 11:29
@Author: micheng. <safemonitor@outlook.com>
@File: urls.py
"""

from django.conf.urls import url
from django.urls import path

from apps.application.views.diagnosis import ArtHasView, ArtHasInstallView, ListServiceNameView

urlpatterns = [
    url(r'^(?P<version>[v1|v2]+)/diagnosis$', ArtHasView.as_view(), name='arthas'),
    url(r'^(?P<version>[v1|v2]+)/diagnosis/agent$', ArtHasInstallView.as_view(), name='install_arthas'),
    url(r'^(?P<version>[v1|v2]+)/diagnosis/service/list$', ListServiceNameView.as_view(), name='list_service_name'),

]
