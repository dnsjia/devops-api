#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
# @File  : scale.py
# @Author: 往事随风
# @Email: gujiwork@outlook.com
# @Date  : 2021/5/31
# @Desc  :
"""

import logging
import time

from rest_framework.views import APIView
from kubernetes import client, config

from utils.authorization import MyAuthentication
from utils.http_response import APIResponse
from utils.permissions import MyPermission

logger = logging.getLogger('default')
config.load_kube_config()
apps_v1 = client.AppsV1Api()


class DeploymentScaleViews(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def post(self, request, *args, **kwargs):
        """
        deployment 扩缩容
        :param request:
        :return:
        """
        if request.user.is_superuser:
            data = request.data
            deployment_number = int(data.get('scaleNumber', 1))
            body = {
                "api_version": "v1",
                "kind": "deployment",
                "spec": {"replicas": deployment_number}
            }

            def deployment_status():
                is_deployment_version = apps_v1.patch_namespaced_deployment_status(name=data.get('name'),
                                                                                   namespace=data.get('namespace'),
                                                                                   body=body,
                                                                                   async_req=True)
                is_deployment_status = is_deployment_version.get()
                is_deployment_status = is_deployment_status.__dict__
                is_deployment_version = is_deployment_status['_metadata'].__dict__

                return is_deployment_version['_generation']

            old_version = deployment_status()
            try:
                ret = apps_v1.patch_namespaced_deployment_scale(name=data.get('name'), namespace=data.get('namespace'), body=body)
                time.sleep(1)

                # body= async_req=True 异步任务 print(ret.get()) 取任务结果
            except Exception as e:
                print(e.args)
                logger.error('Pod缩放异常%s' % str(e.args))
                return APIResponse(errcode=500, errmsg='Pod缩放异常!')
            time.sleep(1)
            new_version = deployment_status()

            if new_version > old_version:
                logger.info('Pod缩放成功:%s, version:%s' % (str(ret), str(old_version)))
                return APIResponse(data={'msg': 'Pod缩放成功'})
            else:
                return APIResponse(data={"msg": "当前版本无变化！"})
        logger.warning('%s用户无权限操作' % str(request.user.username))
        return APIResponse(errcode=401, errmsg='你当前无权限操作!')
