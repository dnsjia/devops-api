#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
@Time: 2020/12/2 10:28
@Author: yu.jiang <safemonitor@outlook.com>
@License: Apache License
@File: pod.py
"""

import json
import yaml
import logging
import traceback

from kubernetes.client import ApiException
from kubernetes import client, config
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.account.models import User
from apps.k8s.serializers.pod import PodSerializers
from utils.authorization import MyAuthentication
from utils.http_response import APIResponse
from utils.pagination import MyPageNumberPagination
from utils.permissions import MyPermission

logger = logging.getLogger('default')
config.load_kube_config()
v1 = client.CoreV1Api()


class PodViews(APIView):
    """
    Pod List
    """
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        namespace = request.query_params.dict().get('namespace', 'default')
        try:
            ret = v1.list_namespaced_pod(namespace=namespace)
            tmp_context = []
            for i in ret.items:
                tmp_dict = dict()
                tmp_dict['pod_ip'] = i.status.pod_ip
                tmp_dict['namespace'] = i.metadata.namespace
                from django.utils import timezone
                tmp_dict['create_time'] = timezone.localtime(i.metadata.creation_timestamp).strftime("%Y-%m-%d %H:%M:%S")
                tmp_dict['name'] = i.metadata.name
                tmp_dict['host_ip'] = i.status.host_ip
                tmp_dict['status'] = i.status.to_dict()
                # 当pod处于Pending状态, 此时pod重启次数 i.status.phase 信息为 None
                # 如果为None, 则返回 0
                tmp_dict['restart_count'] = [0 if i.status.container_statuses is None else i.status.container_statuses[0].restart_count][0]
                tmp_context.append(tmp_dict)
            paginator = MyPageNumberPagination()
            page_publish_list = paginator.paginate_queryset(tmp_context, self.request, view=self)
            ps = PodSerializers(page_publish_list, many=True)
            response = paginator.get_paginated_response(ps.data)
            return APIResponse(data=response.data)

        except ApiException as e:
            logger.error(e, str(traceback.format_exc()))
            return APIResponse(errcode=e.status, errmsg=e.body)
        except Exception as e:
            logger.error(e, str(traceback.format_exc()))
            return APIResponse(errcode=1000, errmsg='获取pod信息出错')


class DetailPodView(APIView):
    """
    对具体的Pod操作
    """
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        name = request.query_params.dict().get('pod_name')
        namespace = request.query_params.dict().get('namespace', 'default')
        try:
            ret = v1.read_namespaced_pod(name=name, namespace=namespace)
            pod_yaml = yaml.safe_dump(ret.to_dict())
            ret_tmp = {}
            ret_tmp = ret.to_dict()
            ret_tmp['pod_yaml'] = str(pod_yaml)
            return APIResponse(data=ret_tmp)

        except ApiException as e:
            logger.error(e, str(traceback.format_exc()))
            return APIResponse(errcode=e.status, errmsg=e.body)
        except Exception as e:
            logger.error(e, str(traceback.format_exc()))
            return APIResponse(errcode=9999, errmsg='获取Pod信息失败')

    def delete(self, request, *args, **kwargs):
        name = request.query_params.dict().get('name')
        namespace = request.query_params.dict().get('namespace', 'default')
        # 允许可删除命名空间下的pod
        # allow_delete_namespace_in_pod = ['develop', 'release', 'uat']
        user_obj = User.objects.filter(username=request.user.username).first()
        user_group = user_obj.roles.all()

        logger.info('用户：%s, 请求删除pod: %s, 命名空间：%s' % (str(request.user.username), name, namespace))
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
            ret = v1.delete_namespaced_pod(name=name, namespace=namespace)
            if ret.status is None:
                return APIResponse(data=ret.to_dict())

        except ApiException as e:
            logger.error(e, str(traceback.format_exc()))
            return APIResponse(errcode=e.status, errmsg=e.body)
        except Exception as e:
            logger.error(e, str(traceback.format_exc()))
            return APIResponse(errcode=9999, errmsg='删除失败')

    def put(self, request, *args, **kwargs):
        data = request.data['params']
        if request.data.get('body') is None:
            return APIResponse(errcode=400, errmsg='YAML不能为空')

        logger.info("patch pod：%s" % data)
        body = yaml.safe_load(request.data.get('body'))
        try:
            res = v1.patch_namespaced_pod(namespace=data.get('namespace'), name=data.get('pod_name'), body=body)
            return APIResponse(data=res.to_dict())
        except ApiException as e:
            logger.error("pod更新异常", str(traceback.format_exc()))
            return APIResponse(errcode=e.status, errmsg=str(e.body).encode('utf-8').decode('unicode_escape'))
        except Exception as e:
            logger.error('更新pod失败：%s' % str(traceback.format_exc()))
        return APIResponse(errcode=9999, errmsg='更新pod失败')

    def post(self, request, *args, **kwargs):
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


class PodFromNodeView(APIView):

    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        """
        查看Node节点部署了多少个Pod
        """
        try:
            node_name = request.query_params
            app_v1 = client.CoreV1Api()
            logger.info("List k8s nodes to pods...")
            field_selector = ("spec.nodeName=" + node_name.get("name"))
            res = app_v1.list_pod_for_all_namespaces(field_selector=field_selector)
            return APIResponse(data=res.to_dict())
        except ApiException as e:
            logger.error(e, str(traceback.format_exc()))
            return APIResponse(errcode=e.status, errmsg=e.body)
        except BaseException as e:
            logger.error(e, str(traceback.format_exc()))
            return APIResponse(errcode=9999, errmsg='服务异常')