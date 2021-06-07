#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
# @File  : node.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2020/12/7
# @Desc  :
"""

import logging
import os
import traceback
from collections import defaultdict
from pint import UnitRegistry
from decouple import config as cg

from rest_framework.views import APIView
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException
from django.conf import settings

from apps.k8s.serializers.node import NodeSerializers
from utils.authorization import MyAuthentication
from utils.http_response import APIResponse
from utils.pagination import MyPageNumberPagination
from utils.permissions import MyPermission

logger = logging.getLogger('default')
config.load_kube_config()
v1 = client.CoreV1Api()


class NodeView(APIView):

    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        """
        获取Node节点
        """
        request_id = request.META.get("HTTP_X_REQUEST_ID", None)
        context = {}
        node_all_label = {}
        data = request.query_params
        field_selector = data.get('name', '')  # metadata.name=192.168.1.16
        label_selector = data.get('label', '')  # beta.kubernetes.io/arch=amd64
        if label_selector is not None and label_selector != '':
            ret = v1.list_node(label_selector=label_selector)
        else:
            if field_selector is not None and field_selector != '':
                try:
                    ret = v1.list_node(field_selector="metadata.name=" + field_selector)
                except ApiException as e:
                    logger.error('获取节点信息失败:%s' % e.body)
                    return APIResponse(errcode=e.status, errmsg=e.body, request_id=request_id)
            else:
                ret = v1.list_node()
        try:
            tmp_context = []
            for node in ret.items:
                tmp_dict = dict()
                tmp_dict['host'] = node.status.addresses[0].address
                tmp_dict['hostname'] = node.status.addresses[1].address
                tmp_dict['labels'] = node.metadata.namespace
                tmp_dict['capacity'] = node.status.capacity
                tmp_dict['allocatable'] = node.status.allocatable
                tmp_dict['name'] = node.metadata.name
                tmp_dict['status'] = node.status.conditions[-1].status
                tmp_dict['created_time'] = node.metadata.creation_timestamp
                tmp_dict['labels'] = node.metadata.labels
                tmp_dict['unschedule'] = node.spec.unschedulable
                node_info = node.status.node_info
                tmp_dict['node_info'] = node_info.to_dict()
                tmp_dict['creation_timestamp'] = node.metadata.creation_timestamp

                # conditions = node.status.conditions
                conditions_list = []
                for condition in node.status.conditions:
                    conditions = {'last_heartbeat_time': condition.last_heartbeat_time,
                                  'last_transition_time': condition.last_transition_time, 'message': condition.message,
                                  'reason': condition.reason, 'status': condition.status, 'type': condition.type}

                    conditions_list.append(conditions)
                tmp_dict['conditions'] = conditions_list

                # 1.1 计算资源使用
                allocatable = node.status.allocatable
                max_pods = int(int(allocatable["pods"]) * 1.5)
                field_selector = (
                            "status.phase!=Succeeded,status.phase!=Failed," + "spec.nodeName=" + node.metadata.name)
                ureg = UnitRegistry()
                units_dir = os.path.join(settings.UNITS, 'kubernetes_units.txt')
                ureg.load_definitions(units_dir)

                Q_ = ureg.Quantity
                resouces = {"cpu_alloc": Q_(allocatable["cpu"]),
                            "mem_alloc": Q_(allocatable["memory"]).to('dimensionless')}

                # 1.2 计算每台Node节点上部署的Pod数量
                allocated_pods = v1.list_pod_for_all_namespaces(limit=max_pods, field_selector=field_selector)
                total_allocated_pods = len(allocated_pods.items)
                tmp_dict['allocated_pods'] = total_allocated_pods

                # 1.3 compute the allocated resources
                cpu_reqs, cpu_limits, mem_reqs, mem_limits = [], [], [], []
                for pod in allocated_pods.items:
                    for container in pod.spec.containers:
                        res = container.resources
                        reqs = defaultdict(lambda: 0, res.requests or {})
                        lmts = defaultdict(lambda: 0, res.limits or {})
                        cpu_reqs.append(Q_(reqs["cpu"]).to('m'))
                        mem_reqs.append(Q_(reqs["memory"]).to('dimensionless'))
                        cpu_limits.append(Q_(lmts["cpu"]).to('m'))
                        mem_limits.append(Q_(lmts["memory"]).to('dimensionless'))
                resouces["cpu_req"] = sum(cpu_reqs)
                resouces["cpu_lmt"] = sum(cpu_limits)
                resouces["cpu_req_per"] = (resouces["cpu_req"] / resouces["cpu_alloc"] * 100).to('dimensionless')
                resouces["cpu_lmt_per"] = (resouces["cpu_lmt"] / resouces["cpu_alloc"] * 100).to('dimensionless')
                resouces["mem_req"] = sum(mem_reqs)
                resouces["mem_lmt"] = sum(mem_limits)
                resouces["mem_req_per"] = (resouces["mem_req"] / resouces["mem_alloc"] * 100).to('dimensionless')
                resouces["mem_lmt_per"] = (resouces["mem_lmt"] / resouces["mem_alloc"] * 100).to('dimensionless')
                # 1.4 返回不带dimensionless单位的值， (8, dimensionless)
                req_limit_dict = {}
                for k, v in resouces.items():
                    value = str(v).split()[0]
                    req_limit_dict[k] = float(value)
                tmp_dict['resouces'] = req_limit_dict

                tmp_context.append(tmp_dict)

            # 对label进行去重
            for label in tmp_context:
                label_dict = label['labels']
                for label_k, label_v in label_dict.items():
                    # print(label_k, label_v)
                    # if label_v == "" or label_v == None:
                    #    pass
                    node_all_label.update({label_k: label_v})

            paginator = MyPageNumberPagination()
            page_publish_list = paginator.paginate_queryset(tmp_context, self.request, view=self)
            queryset = NodeSerializers(page_publish_list, many=True)
            response = paginator.get_paginated_response(queryset.data)
            context = response.data
            return APIResponse(data=context, node_all_label=node_all_label)
        except ApiException as e:
            logger.error(e)
            return APIResponse(errcode=e.status, errmsg=e.body)

        except Exception as e:
            logger.error('获取节点信息失败：%s' % str(traceback.format_exc()), e)
            return APIResponse(errmsg= '获取失败,%s' % e, errcode=1000, request_id=request_id)

    def put(self, request, *args, **kwargs):
        """
        设置Node节点为不可调度
        在后续进行应用部署时，Pod不会再调度到该节点。
        """
        data = request.data
        node_name = data.get('name')
        logger.info("节点：%s，设置为不可调度" % node_name)
        try:
            node_status = v1.read_node_status(name=node_name)
            node_status.spec.unschedulable = True
            res = v1.patch_node(name=node_name, body=node_status)
            return APIResponse(data={'unschedulable': res.spec.unschedulable})
        except ApiException as e:
            logger.error(e)
            return APIResponse(errcode=e.status, errmsg=e.body)
        except BaseException as e:
            logger.error("设置Node节点为不可调度出现异常，节点名：%s, 异常原因：%s" % (node_name, str(e)))
            logger.error(traceback.format_exc())
            return APIResponse(errcode=9999, errmsg=str(e))

    def delete(self, request, *args, **kwargs):
        """
        移除Node节点
        移除节点会涉及Pod迁移，可能会影响业务，请在业务低峰期操作。执行移除后台会把当前节点设置为不可调度状态。
        """
        data = request.query_params
        node_name = data.get('node_name')
        logger.info("Deleting k8s node {}...".format(node_name))
        try:
            # TODO 暂时不开启
            logger.info("节点：%s，设置为不可调度" % node_name)
            node_status = v1.read_node_status(name=node_name)
            node_status.spec.unschedulable = True
            res = v1.patch_node(name=node_name, body=node_status)
            logger.info("节点：%s, 开始排空Pod" % node_name)
            response = v1.list_pod_for_all_namespaces(field_selector="spec.nodeName=%s" % node_name)
            for pod in response.items:
                logger.info("Deleting pod: %s namespace: %s node: %s" %(pod.metadata.name, pod.metadata.namespace, node_name))
                del_ops = client.V1DeleteOptions()
                del_ops.grace_period_seconds = 0
                body = client.V1beta1Eviction(delete_options=del_ops, metadata=pod.metadata)
                # 选择排空节点（同时设置为不可调度），在后续进行应用部署时，则Pod不会再调度到该节点，并且该节点上由DaemonSet控制的Pod不会被排空。
                # kubectl drain cn-beijing.i-2ze19qyi8votgjz12345 --grace-period=120 --ignore-daemonsets=true
                v1.create_namespaced_pod_eviction(name=pod.metadata.name, namespace=pod.metadata.namespace, body=body, async_req=True)
            logger.info("开始移除Node节点, NodeName: %s" % node_name)
            # TODO 暂时不开启
            # v1.delete_node(name=node_name, async_req=True)
            logger.info("移除节点已放入后台任务")
        except ApiException as e:
            logger.info("Exception when calling CoreV1Api->delete_node: {}".format(e))
            return APIResponse(errcode=e.status, errmsg=e.body)

        return APIResponse()

    def post(self, request, *args, **kwargs):
        """
        添加Node 节点
        """
        pass


class DarinNodeAndPod(APIView):

    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        """
        排空节点
        """
        data = request.query_params
        node_name = data.get('node_name')

        try:
            logger.info("节点：%s，设置为不可调度" % node_name)
            node_status = v1.read_node_status(name=node_name)
            node_status.spec.unschedulable = True
            res = v1.patch_node(name=node_name, body=node_status)
            logger.info("节点：%s, 开始排空Pod" % node_name)
            response = v1.list_pod_for_all_namespaces(field_selector="spec.nodeName=%s" % node_name)
            for pod in response.items:
                logger.info("Deleting pod: %s namespace: %s node: %s" %(pod.metadata.name, pod.metadata.namespace, node_name))
                del_ops = client.V1DeleteOptions()
                del_ops.grace_period_seconds = 0
                body = client.V1beta1Eviction(delete_options=del_ops, metadata=pod.metadata)
                # 选择排空节点（同时设置为不可调度），在后续进行应用部署时，则Pod不会再调度到该节点，并且该节点上由DaemonSet控制的Pod不会被排空。
                # kubectl drain cn-beijing.i-2ze19qyi8votgjz12345 --grace-period=120 --ignore-daemonsets=true
                v1.create_namespaced_pod_eviction(name=pod.metadata.name, namespace=pod.metadata.namespace, body=body)
        except ApiException as e:
            logger.error(e)
            return APIResponse(errcode=e.status, errmsg=e.body)
        except BaseException as e:
            return APIResponse(errcode=9999, errmsg=str(e))

        return APIResponse(data={'unschedulable': res.spec.unschedulable, 'evict_pod': True})


class NodeDetailView(APIView):

    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        data = request.query_params
        node_name = data.get('node_name')
        res = v1.read_node_status(name=node_name)
        return APIResponse(data=res.to_dict())


class NodeEventsView(APIView):

    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        data = request.query_params
        node_name = data.get('node_name')
        res = v1.list_event_for_all_namespaces(field_selector="involvedObject.name={}".format(node_name))
        return APIResponse(data=res.to_dict())


class NodeMetrics(APIView):

    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        global url
        api_metrics_url = cg('API_METRICS_URL')
        data = request.query_params
        node_name = data.get('node_name')
        metrics_name = data.get('metrics_name')
        headers = {
            'token': cg('API_METRICS_TOKEN')
        }
        import requests
        if data.get('metrics_name') == 'cpu':
            url = f'{api_metrics_url}/api/v1/namespaces/kube-system/services/heapster/proxy/api/v1/model/nodes/{node_name}/metrics/{metrics_name}/usage_rate'
        elif data.get('metrics_name') == 'memory':
            url = f'{api_metrics_url}/api/v1/namespaces/kube-system/services/heapster/proxy/api/v1/model/nodes/{node_name}/metrics/{metrics_name}/usage'
            # url = f'{api_metrics_url}/api/v1/namespaces/kube-system/services/heapster/proxy/api/v1/model/nodes/{node_name}/metrics/{metrics_name}/working_set'

        print(url)
        try:
            res = requests.get(url=url, headers=headers)
            print(res.text)
            return APIResponse(data=res.json())
        except BaseException:
            return APIResponse(errcode=9999, errmsg="获取指标异常")

