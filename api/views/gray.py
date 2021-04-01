#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
@Author: 风哥
@Mail: gujiwork@outlook.com
@File:gray.py
@Time:2020/10/20 16:30
"""
import traceback
import json
import re
from decouple import config
import redis
from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from api.models import GrayType, GrayDomain
from api.utils.authorization import MyAuthentication
from api.utils.permissions import MyPermission
from utils.rest_page import StandardResultsSetPagination
from utils.serializer import GrayModelSerializers, GrayDomainModelSerializers
import logging
logger = logging.getLogger('default')


class GrayServerView(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        """
        /api/v1/gray/list
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:

            query_project = GrayType.objects.all()
            paginator = StandardResultsSetPagination()
            gray_list = paginator.paginate_queryset(query_project, self.request, view=self)
            serializer_gray_info = GrayModelSerializers(gray_list, many=True)
            gray_page = paginator.get_paginated_response(serializer_gray_info.data)
            return Response(gray_page.data)

        except BaseException as e:
            logger.error('系统异常, 异常原因: %s' % str(traceback.format_exc()), e)
            return JsonResponse(data={
                "errcode": "1006",
                "msg": "系统异常, 请刷新重试!",
                "data": "null"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR, json_dumps_params={'ensure_ascii': False})


class GrayDomainView(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        """
        灰度规则
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        query_gray_domain = GrayDomain.objects.all()
        paginator = StandardResultsSetPagination()
        gray_domain_list = paginator.paginate_queryset(query_gray_domain, self.request, view=self)
        serializer_gray_info = GrayDomainModelSerializers(gray_domain_list, many=True)
        gray_domain_page = paginator.get_paginated_response(serializer_gray_info.data)
        return Response(gray_domain_page.data)

    def post(self, request, *args, **kwargs):
        """
        修改灰度规则
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        if not request.user.is_superuser:
            return JsonResponse(data={'errcode': 403, 'msg': '无权限添加', 'data': 'null'})

        try:
            res = redis.Redis(host=config('REDIS_HOST'), port=6379, password=config('REDIS_PASS'), db=0)
            data = json.loads(request.body.decode('utf-8'))['params']
            rule_type = data.get('rulesType')
            domain = data.get('domain').replace('.', '-')
            obj = GrayDomain.objects.filter(domain_name=data.get('domain')).first()
            user = request.user.name

            if not rule_type is None:
                gray_content = data.get('grayContent')
                if rule_type == "UserAgent":
                    try:
                        with transaction.atomic():
                            Gray = GrayType.objects.create(gray_domain_id=obj.id,
                                                           gray_type=rule_type,
                                                           match_content=gray_content,
                                                           match_key=gray_content,
                                                           match_value=1, creator_name=user)
                            Gray.save()
                            res.hset(name=domain + "_UserAgent", key=gray_content, value=1)
                            logger.info("UserAgent规则创建成功, 创建人:%s" % str(request.user.name))
                            return JsonResponse(data={"msg": "UserAgent规则创建成功", "errcode": 0})

                    except Exception as e:
                        logger.error('添加灰度规则失败, 异常原因: %s' % str(traceback.format_exc()), e)
                        pass

                elif rule_type == "Cookie":
                    try:
                        cookie_content = gray_content.split('=')
                        cookie_key = cookie_content[0]
                        cookie_value = cookie_content[1]
                    except IndexError as e:
                        logger.warning('灰度规则不正确%s， 请检查格式！' % str(e))
                        return JsonResponse(data={"msg": "规则创建失败,格式错误！", "errcode": 9999})
                    try:
                        with transaction.atomic():
                            Gray = GrayType.objects.create(gray_domain_id=obj.id,
                                                           gray_type=rule_type,
                                                           match_content=gray_content,
                                                           match_key=cookie_key,
                                                           match_value=cookie_value, creator_name=user)
                            Gray.save()
                            res.hset(name=domain + "_Cookie", key=cookie_key, value=cookie_value)
                            logger.info("Cookie规则创建成功, 创建人:%s" % str(request.user.name))
                            return JsonResponse(data={"msg": "Cookie规则创建成功", "errcode": 0})
                    except Exception as e:
                        logger.error('添加灰度规则出错, 异常原因: %s' % str(traceback.format_exc()))

                elif rule_type == "IP":
                    # 精确的匹配给定的字符串是否是IP地址
                    if re.match(
                            r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",
                            gray_content):
                        logger.info("灰度IP地址校验通过：%s" % str(gray_content))
                    else:
                        logger.warning("IP invaild, 灰度IP规则无效")
                        return JsonResponse(data={'errcode': 9999, 'msg': 'ip地址格式错误！'})

                    try:
                        with transaction.atomic():
                            Gray = GrayType.objects.create(gray_domain_id=obj.id,
                                                           gray_type=rule_type,
                                                           match_content=gray_content,
                                                           match_key=gray_content,
                                                           match_value=1, creator_name=user)
                            Gray.save()
                            res.hset(name=domain + "_IP", key=gray_content, value=1)
                            logger.info("IP规则创建成功, 创建人:%s" % str(request.user.name))
                            return JsonResponse(data={"msg": "IP规则创建成功", "errcode": 0})

                    except Exception as e:
                        logger.error('添加灰度规则出错, 异常原因: %s' % str(traceback.format_exc()), e)
                        pass

                elif rule_type == "MQSwitch":
                    '''
                    Trip-Service 启动后Java代码先取本机IP，再从redis hash GRAY_IP_MQ中取到灰度ip地址,开1、关0
                    如果ip存在GRAY_IP_MQ中则进行mq的灰度, mq灰度机制是读取trip-service mq配置文件拼接新的mq topic名称
                    如： mq的topic名称为 FLIGHT , 拼接后的新mq topic名称为FLIGHT_Gray
                    '''
                    try:
                        with transaction.atomic():
                            Gray = GrayType.objects.create(gray_domain_id=obj.id,
                                                           gray_type=rule_type,
                                                           match_content=gray_content,
                                                           match_key=gray_content,
                                                           match_value=1, creator_name=user)
                            Gray.save()
                            res.hset(name="GRAY_IP_MQ", key=gray_content, value=1)
                            logger.info("MQSwitch规则创建成功, 创建人:%s" % str(request.user.name))
                            return JsonResponse(data={"msg": "MQSwitch规则创建成功", "errcode": 0})

                    except Exception as e:
                        logger.error(e)

                else:
                    logger.error("灰度规则错误")
                    return JsonResponse(data={"msg": "灰度规则错误", "errcode": 500})

        except BaseException as e:
            logger.error('添加灰度规则失败, 异常原因: %s' % str(traceback.format_exc()), e)
            return JsonResponse(data={'errcode': 500, 'msg': '添加失败'})

    def delete(self, request, *args, **kwargs):
        """
        删除灰度规则
        :param request:
        :param args:
        :param kwargs:
        :return:
        """

        if not request.user.is_superuser:
            return JsonResponse(data={'errcode': 403, 'msg': '无权限删除'})

        try:
            data = request.query_params.dict()
            pk = data.get('id', None)
            if pk is None:
                return JsonResponse({'errcode': 1000, 'msg': '删除异常！'})
            logger.info("开始删除灰度规则,请求body: %s" % str(data) )
            GrayType.objects.filter(id=pk).delete()
            res = redis.Redis(host=config('REDIS_HOST'), port=6379, password=config('REDIS_PASS'), db=0)
            gray_hash_name = str(data.get('gray_domain')).replace('.','-') + '_' + str(data.get('gray_type'))
            gray_hash_key = data.get('match_key')

            del_hash_key_result = res.hdel(gray_hash_name, gray_hash_key)
            logger.info('删除redis存放信息,hash_name={}, hash_key={}, result={}'.format(gray_hash_name, gray_hash_key, del_hash_key_result))
            get_hash_key_result = res.hget(gray_hash_name, gray_hash_key)

            if get_hash_key_result is not None:
                raise Exception('灰度规则删除失败！')
            logger.info("灰度规则删除成功, 操作人: %s" % str(request.user.name))
            return JsonResponse(data={'errcode': 0, 'msg': '删除成功！'})
        except Exception as e:
            logger.error('删除灰度规则失败, 异常原因: %s' % str(traceback.format_exc()), e)
            return JsonResponse(data={'errcode': 9999, 'msg': '删除失败！'})
