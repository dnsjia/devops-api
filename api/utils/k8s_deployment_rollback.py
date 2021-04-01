#!/bin/env python3
# -*- coding: utf-8 -*-

"""
@Time: 2020/11/9 15:39
@Author: yu.jiang <safemonitor@outlook.com>
@License: Apache License
@File: k8s_deployment_rollback.py

"""
from kubernetes import client, config
import logging
import traceback
import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent

k8s_api_config = os.path.join(BASE_DIR, 'api', 'utils', 'config_test')
config.load_kube_config(config_file=k8s_api_config)
logger = logging.getLogger('default')
app_v1 = client.ExtensionsV1beta1Api()


class KubernetesApi:

    @classmethod
    def update_deployment(self, deployment_name, namespace, images):
        """
        回滚deployment
        :param deployment_name:  deployment名称
        :param namespace: 命名空间
        :param images: 镜像地址
        :return:
        """
        try:
            deployment = app_v1.read_namespaced_deployment(name=deployment_name, namespace=namespace, )
            # Update container image
            logger.info("deployment image: %s" % (deployment.spec.template.spec.containers[0].image,))
            deployment.spec.template.spec.containers[0].image = images
            # Update the deployment
            api_response = app_v1.patch_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
                body=deployment)
            logger.info("Deployment updated. status='%s'" % str(api_response.status))
            return {'msg': 'success', 'errcode': 0}
        except BaseException as e:
            logger.error(e)
            logger.error("回滚deployment异常，%s" % str(traceback.format_exc()))
            return {'msg': 'fail', 'errcode': 500}

