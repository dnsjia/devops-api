#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
# @File  : deployment.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2020/12/7
# @Desc  :
"""

import logging
import traceback

from django.utils import timezone
from kubernetes.client import ApiException
from rest_framework.views import APIView
from rest_framework.response import Response
from kubernetes import client, config

from apps.account.models import User
from apps.k8s.serializers.deployment import DeploymentSerializers
from utils.authorization import MyAuthentication
from utils.http_response import APIResponse
from utils.pagination import MyPageNumberPagination
from utils.permissions import MyPermission

logger = logging.getLogger('default')
config.load_kube_config()
apps_v1 = client.AppsV1Api()


class DeploymentViews(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    """
    Deployment
    """

    def get(self, request, *args, **kwargs):
        namespace = request.query_params.dict().get('namespace', 'default')
        try:

            ret = apps_v1.list_namespaced_deployment(namespace=namespace)
            tmp_context = []
            for i in ret.items:
                if i.metadata.name == 'trip-service':
                    print(i)

                tmp_dict = dict()
                tmp_dict['name'] = i.metadata.name
                tmp_dict['namespace'] = i.metadata.namespace
                tmp_dict['labels'] = i.metadata.labels
                tmp_dict['create_time'] = timezone.localtime(i.metadata.creation_timestamp).strftime(
                    "%Y-%m-%d %H:%M:%S")
                tmp_dict['image'] = i.spec.template.spec.containers[0].image
                tmp_dict['replicas'] = i.spec.replicas
                tmp_dict['available_replicas'] = i.status.available_replicas
                tmp_dict['ready_replicas'] = i.status.ready_replicas
                tmp_dict['unavailable_replicas'] = i.status.unavailable_replicas
                tmp_dict['updated_replicas'] = i.status.updated_replicas
                tmp_context.append(tmp_dict)
            paginator = MyPageNumberPagination()
            page_publish_list = paginator.paginate_queryset(tmp_context, self.request, view=self)
            ps = DeploymentSerializers(page_publish_list, many=True)
            response = paginator.get_paginated_response(ps.data)
            context = response.data
            return APIResponse(data=context)

        except ApiException as e:
            logger.error(e)
            return APIResponse(errcode=e.status, errmsg=e.body)

        except Exception as e:
            logger.error(str(e))
            logger.error('获取无状态服务异常: %s' % str(traceback.format_exc()))
            return APIResponse(errcode=9999, errmsg="获取无状态服务异常")


class DetailDeploymentViews(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    """
    对具体的Deployment操作
    """

    def get(self, request, *args, **kwargs):
        name = request.query_params.dict().get('name')
        namespace = request.query_params.dict().get('namespace', 'default')
        try:
            ret = apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
            return APIResponse(data=ret.to_dict())
        except Exception as e:
            logger.exception(e)
            # logger.error(traceback.format_exc())
            return APIResponse(errcode=1000, errmsg='获取Deployment信息失败')

    def delete(self, request, *args, **kwargs):
        name = request.query_params.dict().get('name')
        namespace = request.query_params.dict().get('namespace', 'default')
        logger.info("用户: %s, 请求删除deployment: %s, 命名空间：%s" % (request.user.username, name, namespace))

        # 允许可删除命名空间下的deployment
        # allow_delete_namespace_in_deployment = ['develop', 'release', 'uat']
        user_obj = User.objects.filter(username=request.user.username).first()
        user_group = user_obj.roles.all()

        if not request.user.is_superuser:
            if user_group:
                group = str(user_group[0]).strip()
                if group == 'develop' and namespace != 'develop' or namespace != 'dingtalk':
                    return APIResponse(errcode=403, errmsg='无权限删除')
                elif group == 'test' and namespace != 'release' or namespace != 'dingtalk':
                    return APIResponse(errcode=403, errmsg='无权限删除')
                else:
                    return APIResponse(errcode=403, errmsg='无权限删除')
            else:
                return APIResponse(errcode=403, errmsg='无权限删除')

        try:
            ret = apps_v1.delete_namespaced_deployment(name=name, namespace=namespace)
            logger.info(ret)
            return APIResponse(data={'msg': '删除成功'})
        except Exception as e:
            logger.error("删除deployment: %s失败" % name)
            logger.exception(e)
            return APIResponse(errcode=1000, errmsg='删除失败')

    def put(self, request, *args, **kwargs):
        import json
        name = request.data.get('name')
        namespace = request.data.get('namespace', 'default')
        body = request.data.get('body')
        if isinstance(body, str):
            body = json.loads(request.data.get('body'))
        else:
            pass
        metadata = body.get('metadata', '')
        spec = body.get('spec', '')
        context = {'errcode': 0, 'msg': '更新成功!', 'data': ''}
        try:
            old_resp = apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
            old_resp.metadata.annotations = metadata.get('annotations')
            old_resp.metadata.labels = metadata.get('labels')
            old_resp.metadata.name = metadata.get('name')
            old_resp.metadata.namespace = metadata.get('namespace')
            old_resp.metadata.selector = metadata.get('selector')

            old_resp.spec.replicas = spec.get('replicas')
            old_resp.spec.template.spec.affinity = spec.get('template').get('spec').get('affinity')
            for i in range(len(old_resp.spec.template.spec.containers)):
                old_resp.spec.template.spec.containers[i].args = \
                    spec.get('template').get('spec').get('containers')[i].get('args')
                old_resp.spec.template.spec.containers[i].command = \
                    spec.get('template').get('spec').get('containers')[i].get('command')
                old_resp.spec.template.spec.containers[i].env = \
                    spec.get('template').get('spec').get('containers')[i].get('env')
                old_resp.spec.template.spec.containers[i].env_from = \
                    spec.get('template').get('spec').get('containers')[i].get('env_from')
                old_resp.spec.template.spec.containers[i].image = \
                    spec.get('template').get('spec').get('containers')[i].get('image')
                old_resp.spec.template.spec.containers[i].image_pull_policy = \
                    spec.get('template').get('spec').get('containers')[i].get('image_pull_policy')
                old_resp.spec.template.spec.containers[i].lifecycle = \
                    spec.get('template').get('spec').get('containers')[i].get('lifecycle')
                old_resp.spec.template.spec.containers[i].liveness_probe = \
                    spec.get('template').get('spec').get('containers')[i].get('liveness_probe')
                old_resp.spec.template.spec.containers[i].name = \
                    spec.get('template').get('spec').get('containers')[i].get('name')

            apps_v1.patch_namespaced_deployment(name=name, namespace=namespace, body=old_resp)
        except Exception as e:
            context['errcode'] = 1000
            context['msg'] = e
        return Response(context)

    def post(self, request, *args, **kwargs):
        import yaml
        context = {'errcode': 0, 'msg': '部署成功!', 'data': ''}
        namespace = request.data.get('namespace', 'default')
        try:
            body = yaml.safe_load(request.data.get('body'))
            deploy_type = body.get('kind')
            if deploy_type != 'Deployment':
                context['errcode'] = 1000
                context['msg'] = '部署类型错误!'
                return Response(context)
        except Exception as e:
            context['errcode'] = 1000
            context['msg'] = e
            return Response(context)
        try:
            apps_v1.create_namespaced_deployment(namespace=namespace, body=body)
        except Exception as e:
            context['errcode'] = 1000
            context['msg'] = e
        return Response(context)


class DeploymentHistoryVersionViews(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        """
        get deployment rollout history
        """
        try:
            data = request.query_params.dict()
            namespace = data.get('namespace')
            name = data.get('name')

            ret = apps_v1.list_namespaced_replica_set(namespace=namespace)
            rollback_history_data = {}
            for i in ret.items:
                if namespace == i.metadata.namespace and name == i.metadata.owner_references[0].name:
                    rollback_history_data[i.metadata.name] = {
                        "create_time": i.metadata.creation_timestamp,
                        "images": i.spec.template.spec.containers[0].image,
                        "version": int(i.metadata.annotations['deployment.kubernetes.io/revision']),
                        "namespace": i.metadata.namespace,
                        "name": i.metadata.owner_references[0].name,
                    }
            rollback_history_data = sorted(rollback_history_data.values(), key=lambda x: x['version'], reverse=True)
            return APIResponse(data=rollback_history_data)
        except ApiException as e:
            return APIResponse(errcode=e.status, errmsg=e.reason)
        except BaseException as e:
            logger.exception(e)
            return APIResponse(errcode=500, errmsg='获取deployment历史版本异常')

    def post(self, request, *args, **kwargs):
        """
        rollout deployment version
        """

        data = request.data
        version = int(data.get('version'))
        body = {
            # "rollback_to": {"revision": version},  # 新版API
            "rollbackTo": {"revision": version},  # 旧版本API
            "name": data['name']
        }
        try:
            apps_v1 = client.AppsV1beta1Api()
            ret = apps_v1.create_namespaced_deployment_rollback(name=data['name'], namespace=data['namespace'],
                                                                body=body)
            ret = ret.__dict__

            if ret.get('_code') == 200:
                logger.info('Pod回滚成功:%s' % str(ret))
                return APIResponse(data={"msg": "回滚成功！"})

            else:
                logger.error('应用回滚失败:%s' % str(ret))
                return APIResponse(errcode=500, errmsg="应用回滚失败！")

        except ApiException as e:
            return APIResponse(errcode=e.status, errmsg=e.reason)
        except BaseException as e:
            logger.exception(e)
            return APIResponse(errcode=500, errmsg="应用回滚失败！")
