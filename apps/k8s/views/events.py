#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.

# @File  : events.py
# @Author: 往事随风
# @Email: gujiwork@outlook.com
# @Date  : 2021/4/28
# @Desc  :

import logging
import traceback

from kubernetes.client import ApiException
from rest_framework.views import APIView
from kubernetes import client, config

from utils.authorization import MyAuthentication
from utils.http_response import APIResponse
from utils.permissions import MyPermission

config.load_kube_config()
logger = logging.getLogger('default')
app_v2 = client.CoreV1Api()


class EventsView(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        """
        获取Pod、Node事件信息
        """
        data = request.query_params.dict()
        # 如果传递的是Node名称则获取Node的事件, 如果传递的是Pod名称则获取Pod的事件
        name = data.get('name')
        if name:
            try:
                res = app_v2.list_event_for_all_namespaces(
                    field_selector="involvedObject.name={}".format(name))
                return APIResponse(data=res.to_dict())
            except ApiException as e:
                logger.error(e, str(traceback.format_exc()))
                return APIResponse(errcode=e.status, errmsg=e.body)
            except Exception as e:
                logger.error(e, str(traceback.format_exc()))
                return APIResponse(errcode=9999, errmsg='获取事件信息失败')
        else:
            return APIResponse(errcode=404, errmsg='传递的参数不能为空')


class DeploymentEventsView(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        """
        获取Deployment事件信息
        """
        data = request.query_params.dict()
        name = data.get('name')
        namespace = data.get('namespace')
        try:
            app = client.CoreV1Api()
            res = app.list_event_for_all_namespaces(
                field_selector=f"involvedObject.kind=Deployment,involvedObject.name={name},involvedObject.namespace={namespace}"
                )
            return APIResponse(data=res.to_dict())
        except Exception as e:
            logger.exception(e)
            return APIResponse(errcode=500, errmsg='获取deployment事件失败')
