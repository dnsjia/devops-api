#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : pod.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2020/12/7
# @Desc  :
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from kubernetes import client, config
import traceback
from api.utils.authorization import MyAuthentication
from api.utils.permissions import MyPermission
from k8s.serializers.pod import PodSerializers
from api.utils.pagination import MyPageNumberPagination
import logging
logger = logging.getLogger('default')
config.load_kube_config()
v1 = client.CoreV1Api()


class PodViews(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    """
    Pod
    """

    def get(self, request, *args, **kwargs):
        namespace = request.query_params.dict().get('namespace')
        context = {}
        try:
            if namespace:
                ret = v1.list_namespaced_pod(namespace=namespace)
            else:
                ret = v1.list_namespaced_pod(namespace='default')
                # ret = v1.list_pod_for_all_namespaces(watch=False)
            tmp_context = []
            for i in ret.items:
                tmp_dict = dict()
                tmp_dict['pod_ip'] = i.status.pod_ip
                tmp_dict['namespace'] = i.metadata.namespace
                from django.utils import timezone
                tmp_dict['create_time'] = timezone.localtime(i.metadata.creation_timestamp).strftime("%Y-%m-%d %H:%M:%S")
                # print(timezone.localtime(i.metadata.creation_timestamp).strftime("%Y-%m-%d %H:%M:%S"))
                tmp_dict['name'] = i.metadata.name
                tmp_dict['host_ip'] = i.status.host_ip
                tmp_dict['status'] = i.status.phase
                # 当pod处于Pending状态, 此时pod重启次数 i.status.phase 信息为 None
                # 如果为None, 则返回 0
                tmp_dict['restart_count'] = [0 if i.status.container_statuses is None else i.status.container_statuses[0].restart_count][0]
                tmp_context.append(tmp_dict)
            paginator = MyPageNumberPagination()
            page_publish_list = paginator.paginate_queryset(tmp_context, self.request, view=self)
            ps = PodSerializers(page_publish_list, many=True)
            response = paginator.get_paginated_response(ps.data)
            return response
        except Exception as e:
            logger.error('获取pod详细信息出错：%s' % str(traceback.format_exc()))
            context['errcode'] = 1000
            context['msg'] = e
            context['data'] = ''
        return Response(context)


class DetailPodView(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]
    """
    对具体的Pod操作
    """

    def get(self, request, *args, **kwargs):
        name = request.query_params.dict().get('name')
        namespace = request.query_params.dict().get('namespace', 'default')
        context = {'errcode': 0, 'msg': '获取Pod信息成功!', 'data': ''}
        try:
            ret = v1.read_namespaced_pod(name=name, namespace=namespace)
            context['errcode'] = ret.to_dict()
        except Exception as e:
            print(e)
            context['errcode'] = 1000
            context['msg'] = '获取Pod信息失败'
        return Response(context)

    def delete(self, request, *args, **kwargs):
        name = request.query_params.dict().get('name')
        namespace = request.query_params.dict().get('namespace', 'default')
        # 允许可删除命名空间下的pod
        allow_delete_namespace_in_pod = ['dev', 'feiba', 'flyby', 'new', 'test', 'yikuaiban']
        if not request.user.is_superuser:
            if namespace not in allow_delete_namespace_in_pod:
                return JsonResponse(data={'errcode': 403, 'msg': '无权限删除！'})
        logger.info('用户：%s, 请求删除pod: %s, 命名空间：%s' % (str(request.user.username), name, namespace))
        context = {'errcode': 0, 'msg': '删除成功!', 'data': ''}
        try:
            ret = v1.delete_namespaced_pod(name=name, namespace=namespace)
            if ret.status is None:
                context['errcode'] = 1000
                context['msg'] = ret
        except Exception as e:
            logger.error('删除pod失败：%s' % str(traceback.format_exc()))
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
            old_resp = v1.read_namespaced_pod(name=name, namespace=namespace)
            old_resp.metadata.annotations = metadata.get('annotations')
            old_resp.metadata.labels = metadata.get('labels')
            old_resp.metadata.name = metadata.get('name')
            old_resp.metadata.namespace = metadata.get('namespace')

            old_resp.spec.affinity = spec.get('affinity')
            for i in range(len(old_resp.spec.containers)):
                old_resp.spec.containers[i].args = spec.get('containers')[i].get('args')
                old_resp.spec.containers[i].command = spec.get('containers')[i].get('command')
                old_resp.spec.containers[i].env = spec.get('containers')[i].get('env')
                old_resp.spec.containers[i].env_from = spec.get('containers')[i].get('env_from')
                old_resp.spec.containers[i].image = spec.get('containers')[i].get('image')
                old_resp.spec.containers[i].image_pull_policy = spec.get('containers')[i].get('image_pull_policy')
                old_resp.spec.containers[i].lifecycle = spec.get('containers')[i].get('lifecycle')
                old_resp.spec.containers[i].liveness_probe = spec.get('containers')[i].get('liveness_probe')
                old_resp.spec.containers[i].name = spec.get('containers')[i].get('name')
            v1.replace_namespaced_pod(name=name, namespace=namespace, body=old_resp)
        except Exception as e:
            logger.error('更新pod失败：%s' % str(traceback.format_exc()))
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
            if deploy_type != 'Pod':
                context['errcode'] = 1000
                context['msg'] = '部署类型错误!'
                return Response(context)
        except Exception as e:
            logger.error('部署pod异常：%s' % str(traceback.format_exc()))
            context['errcode'] = 1000
            context['msg'] = e
            return Response(context)

        try:
            v1.create_namespaced_pod(namespace=namespace, body=body)
        except Exception as e:
            logger.error('部署pod异常：%s' % str(traceback.format_exc()))
            context['errcode'] = 1000
            context['msg'] = e
        return Response(context)
