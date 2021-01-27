#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : deployment.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2020/12/7
# @Desc  :

from rest_framework.views import APIView
from rest_framework.response import Response
from kubernetes import client, config
from api.utils.authorization import MyAuthentication
from api.utils.permissions import MyPermission
from k8s.serializers.deployment import DeploymentSerializers
from api.utils.pagination import MyPageNumberPagination
import logging
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
        namespace = request.query_params.dict().get('namespace')
        context = {'errcode': 0, 'msg': '获取Deployment成功!', 'data': ''}
        try:
            if namespace:
                ret = apps_v1.list_namespaced_deployment(namespace=namespace)
            else:
                ret = apps_v1.list_deployment_for_all_namespaces()
            tmp_context = []
            for i in ret.items:
                tmp_dict = dict()
                tmp_dict['name'] = i.metadata.name
                tmp_dict['namespace'] = i.metadata.namespace
                tmp_dict['labels'] = i.metadata.labels
                from django.utils import timezone
                tmp_dict['create_time'] = timezone.localtime(i.metadata.creation_timestamp).strftime("%Y-%m-%d %H:%M:%S")
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
            return response

        except Exception as e:
            context['errcode'] = 1000
            context['msg'] = e
        return Response(context)


class DetailDeploymentViews(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    """
    对具体的Deployment操作
    """

    def get(self, request, *args, **kwargs):
        name = request.query_params.dict().get('name')
        namespace = request.query_params.dict().get('namespace', 'default')
        context = {'errcode': 0, 'msg': '获取Deployment信息成功!', 'data': ''}
        try:
            ret = apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
            context['data'] = ret.to_dict()
        except Exception as e:
            print(e)
            context['errcode'] = 1000
            context['msg'] = '获取Deployment信息失败'
        return Response(context)

    def delete(self, request, *args, **kwargs):
        name = request.query_params.dict().get('name')
        namespace = request.query_params.dict().get('namespace', 'default')
        context = {'errcode': 0, 'msg': '删除成功!', 'data': ''}
        try:
            ret = apps_v1.delete_namespaced_deployment(name=name, namespace=namespace)
            if ret.status is None:
                context['errcode'] = 1000
                context['msg'] = ret
        except Exception as e:
            print(e)
            context['errcode'] = 1000
            context['msg'] = '删除失败'
        return Response(context)

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
