#!/bin/env python3
# -*- coding: utf-8 -*-

"""
@Time: 2020/9/27 16:55
@Author: yu.jiang <safemonitor@outlook.com>
@License: Apache License
@File: nginx.py

"""

import json
import traceback
import requests
from decouple import config
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.forms import model_to_dict
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from api.models import VirtualHost
from api.utils.authorization import MyAuthentication
from api.utils.permissions import MyPermission
from utils.rest_page import StandardResultsSetPagination
from utils.serializer import NginxListModelSerializers
import logging
logger = logging.getLogger('default')


class QueryNginxView(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        """
        获取虚拟主机信息
        :param request:
        :param args:
        :param kwargs:
        :return:
        """

        try:
            keywords = request.GET.get('keywords', None)
            if keywords is not None:
                keywords = keywords.strip()
                query_host = VirtualHost.objects.filter(
                    Q(internet_port__icontains=keywords) | Q(upstream_name__icontains=keywords) |
                    Q(forward_address__icontains=keywords) | Q(creator_name__icontains=keywords)).order_by('id')
                paginator = StandardResultsSetPagination()
                page_nginx_list = paginator.paginate_queryset(query_host, self.request, view=self)
                serializer_nginx_info = NginxListModelSerializers(page_nginx_list, many=True)
                page_nginx = paginator.get_paginated_response(serializer_nginx_info.data)
                return Response(page_nginx.data)

            obj_nginx_list = VirtualHost.objects.all().order_by('-id')
            paginator = StandardResultsSetPagination()
            page_nginx_list = paginator.paginate_queryset(obj_nginx_list, self.request, view=self)
            serializer_nginx_info = NginxListModelSerializers(page_nginx_list, many=True)
            page_nginx = paginator.get_paginated_response(serializer_nginx_info.data)
            return Response(page_nginx.data)

        except BaseException as e:
            logger.error('获取虚拟主机异常, 异常原因: %s' % str(traceback.format_exc()))
            return JsonResponse(data={
                "errcode": "1006",
                "msg": "系统异常, 请刷新重试!",
                "data": e
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR, json_dumps_params={'ensure_ascii': False})


class AddHostNginxView(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def post(self, request, *args, **kwargs):
        """
        增加nginx 虚拟主机
        :param request:
        :param args:
        :param kwargs:
        :return:
        """

        creator_name = request.user.name
        if request.method == 'POST':
            try:
                request_data = json.loads(request.body.decode('utf-8'))['params']
                logger.info('新增虚拟主机data={%s}' % request_data)
                internet_port = request_data.get('internet_port')
                if internet_port is None or internet_port == '':
                    return JsonResponse(data={'errcode': 400, 'msg': '端口不能为空！'})

                if VirtualHost.objects.filter(internet_port=internet_port).count() >= 1:
                    return JsonResponse(data={'errcode': 400, 'msg': '端口已存在！'})

                # elif int(internet_port) < 1100 or int(internet_port) >= 1201:
                #     return JsonResponse(data={'status': 400, 'msg': '端口范围不能小于1100大于1200！'})

                else:
                    upstream_name = request_data.get('upstream_name')
                    if upstream_name is None or upstream_name == '':
                        return JsonResponse(data={'errcode': 400, 'msg': '名称不能为空！'})

                    elif VirtualHost.objects.filter(upstream_name=upstream_name).count() >= 1:
                        return JsonResponse(data={'errcode': 400, 'msg': '名称已存在！'})

                    forward_address = request_data.get('forward_address')
                    if forward_address is None or forward_address == '':
                        return JsonResponse(data={'errcode': 400, 'msg': '转发地址不能为空！'})

                    else:
                        port = request_data.get('port')
                        if port is None or port == '':
                            return JsonResponse(data={'errcode': 400, 'msg': '端口不能为空！'})

                        elif int(port) > 65535 or int(port) < 0:
                            return JsonResponse(data={'errcode': 400, 'msg': '端口不能超过65535或者小于0！'})

                        else:
                            remarks = request_data.get('remarks')
                            if remarks is None or remarks == '':
                                return JsonResponse(data={'errcode': 400, 'msg': '备注不能为空！'})

                consul_headers = {
                    "Content-Type": "application/json"
                }
                consul_data = {
                    "Datacenter": "dc1",
                    "Node": upstream_name,
                    "Address": forward_address,
                    "Service": {
                        "Id": forward_address + ':' + port,
                        # "Service": 'tomcat',
                        "Service": upstream_name,
                        "tags": [str(internet_port)],
                        "Port": int(port)
                    }
                }

                try:
                    with transaction.atomic():
                        logger.info('用户：%s, 新增虚拟主机：%s' % (creator_name, consul_data))
                        rsp = requests.put(url=config('CONSUL_API') + '/v1/catalog/register', data=json.dumps(consul_data),
                                           headers=consul_headers)
                        logger.info('Consul接口返回信息：%s' % rsp.content)
                        # 数据组装插入数据库
                        orm_data = {
                            'internet_port': internet_port,
                            'upstream_name': upstream_name,
                            'forward_address': forward_address,
                            'port': port,
                            'remarks': remarks,
                            'creator_name': creator_name
                        }
                        logger.info("原始报文: %s" % orm_data)
                        if rsp.content.decode('utf-8') == "true":
                            VirtualHost.objects.create(**orm_data)
                            return JsonResponse(data={'errcode': 0, 'msg': '新增成功'})

                        else:
                            VirtualHost.objects.filter(internet_port=internet_port, upstream_name=upstream_name,
                                                       forward_address=forward_address, port=port, remarks=remarks,
                                                       creator_name=creator_name).delete()
                            logger.info('新增虚拟主机失败, 异常原因：%s' % rsp.content)
                            return JsonResponse(data={'errcode': 400, 'msg': '新增失败'})

                except IntegrityError:
                   logger.error(str(traceback.format_exc()))

            except BaseException as e :
                logger.info('新增虚拟主机失败,异常原因：%s' % str(traceback.format_exc()), e)
                return JsonResponse(data={'errcode': 400, 'msg': '新增失败'})

    def put(self, request, *args, **kwargs):
        """
        更新主机
        :param request:
        :param args:
        :param kwargs:
        :return:
        """

        request_data = json.loads(request.body.decode('utf-8'))['params']
        user = request.user
        create_user = VirtualHost.objects.get(id=request_data.get('id'))
        create_user = model_to_dict(create_user)['creator_name']

        if not request.user.is_superuser:
            if user.name != create_user.strip():
                return JsonResponse(data={'errcode': 403, 'msg': '该主机不属于你,你无权操作！'})

        consul_headers = {
            "Content-Type": "application/json"
        }
        logger.info('更新主机请求报文 data={%s}' % request_data)
        try:
            get_service = requests.get(
                url=config('CONSUL_API') + '/v1/catalog/service/{}'.format(request_data.get('upstream_name')),
                headers=consul_headers)
            rsp_consul = json.loads(get_service.content.decode('utf-8'))
            logger.info('获取Upstream服务返回信息: %s' % rsp_consul)

        except BaseException as e:
            logger.error('获取服务信息异常，更新主机失败！异常原因：%s' % str(traceback.format_exc()), e)
            logger.error(str(get_service.content.decode('utf-8')))
            return JsonResponse(data={'errcode': 500, 'msg': '更新失败！'})

        try:
            service_id = rsp_consul[0]['ServiceID']
            if service_id:
                put_consul_data = {
                    "Datacenter": "dc1",
                    "Node": str(request_data.get('upstream_name')),
                    "Address": str(request_data.get('forward_address')),
                    "Service": {
                        "Id": str(service_id),
                        "Service": str(request_data.get('upstream_name')),
                        "tags": [str(request_data.get('internet_port'))],
                        "Port": int(request_data.get('port'))
                    }
                }

                logger.info('请求consul更新服务, data={%s}' % str(put_consul_data))
                register_put_url = config('CONSUL_API') + '/v1/catalog/register'
                rsp = requests.put(url=register_put_url, headers=consul_headers, data=json.dumps(put_consul_data))
                logger.info('请求consul更新服务, consul返回data={%s}' % str(rsp.content.decode('utf-8')))

                if rsp.content.decode('utf-8'):
                    put_orm_data = {
                        'forward_address': request_data['forward_address'],
                        'port': request_data['port'],
                        'remarks': request_data['remarks']
                    }
                    with transaction.atomic():
                        VirtualHost.objects.filter(internet_port=request_data['internet_port'],
                                                   upstream_name=request_data['upstream_name']).update(**put_orm_data)
                        logger.info("主机更新成功, 操作人: %s, data={%s}" % (str(request.user.name), str(put_orm_data)))
                        return JsonResponse(data={'errcode': 0, 'msg': '更新成功'})

                else:
                    logger.error('请求consul更新服务失败, consul返回信息={%s}' % str(rsp.content.decode('utf-8')))
                    return JsonResponse(data={'errcode': 9999, 'msg': '更新失败'})

        except IndexError:
            logger.error('获取ServiceID失败, %s' % str(traceback.format_exc()))
            return JsonResponse(data={'errcode': 9999, 'msg': '更新失败'})

        except BaseException as e:
            logger.error('更新虚拟主机失败, 异常原因: %s' % str(traceback.format_exc()), e)
            return JsonResponse(data={'errcode': 9999, 'msg': '更新失败'})

    def delete(self, request, *args, **kwargs):
        """
        删除虚拟主机
        :param request:
        :param args:
        :param kwargs:
        :return:
        """

        if not request.user.is_superuser:
            return JsonResponse(data={'errcode': 403, 'msg': '你无权删除,请联系管理员！'})
        pk = request.GET.get('id')
        try:
            host = VirtualHost.objects.filter(id=pk).values().first()
            get_service = requests.get(
                url=config('CONSUL_API') + '/v1/catalog/service/{}'.format(host.get('upstream_name')),
                headers={"Content-Type": "application/json"})

            rsp_consul = json.loads(get_service.content.decode('utf-8'))
            logger.info('删除前获取Upstream服务返回信息: %s' % rsp_consul)
            service_id = rsp_consul[0]['ServiceID']
            del_data = {
                "Datacenter": "dc1",
                "Node": host.get('upstream_name'),
                "ServiceId": str(service_id)
            }
            logger.info('删除consul请求数据=%s' % str(del_data))
            rsp = requests.put(
                url=config('CONSUL_API') + '/v1/catalog/deregister',
                headers={"Content-Type": "application/json"},
                data=json.dumps(del_data)).content.decode('utf-8')

            if rsp:
                host = VirtualHost.objects.filter(id=pk).delete()
                logger.info('consul服务删除成功, 返回信息：%s' % rsp)
                return JsonResponse(data={'errcode': 0, 'msg': '删除成功'})

            else:
                logger.error('删除consul服务失败, consul返回信息：%s' % rsp)
                return JsonResponse(data={'errcode': 500, 'msg': rsp})

        except BaseException as e:
            logger.error('删除服务失败, 异常返回信息：%s' % str(traceback.format_exc()), e)
            return JsonResponse(data={'errcode': 500, 'msg': '删除失败'})
