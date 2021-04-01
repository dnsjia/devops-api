#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : es_manage.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2020/11/21
# @Desc  :
from decouple import config
from django.http import JsonResponse
from elasticsearch import Elasticsearch
from rest_framework.views import APIView
import traceback
from api.utils.permissions import MyPermission
from devops.settings import BASE_DIR
from api.utils.authorization import MyAuthentication
from elasticsearch.exceptions import NotFoundError
from time import strftime, localtime
import logging
import os
import json
logger = logging.getLogger('default')


class ElasticSearchView(APIView):

    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        """
        获取所有索引名称
        """
        try:
            client = Elasticsearch(config('ES_URL'), http_auth=(config('ES_USER'), config('ES_PASS')))
            rst = client.indices.get_alias("*")
            index_list = []
            id = 0
            for index in rst:
                id += 1
                # 索引以 . 开头的不做处理忽略掉, 如.monitoring*
                if str(index).startswith('.'):
                    continue
                else:
                    index_list.append({'id': id, 'index_name': index})

            data = {
                'data': index_list,
                'errcode': 0
            }
            return JsonResponse(data=data)
        except BaseException as e:
            logger.error('请求异常，%s' %(str(traceback.format_exc())), e)
            return JsonResponse(data={'errcode': 500, 'msg': '请求异常,请稍后再试！'})

    def post(self, request, *args, **kwargs):
        """
        查询es , get方法根据文档id查询, post方法根据传递body查询
        """

        request_data = request.data['params']
        logger.info('用户={%s}，请求查询, 请求参数：%s' %(request.user.name, request_data))
        client = Elasticsearch(config('ES_URL'), http_auth=(config('ES_USER'), config('ES_PASS')))
        file_name = str(request.user.username) + '_' + str(strftime('%Y%m%d%H%M%S', localtime()) + '.json')
        json_file = os.path.join(BASE_DIR, 'files', 'es', file_name)
        logger.info('查询结果保存：%s' % str(json_file))
        if not os.path.exists(os.path.join(BASE_DIR, 'files', 'es')):
            os.makedirs(os.path.join(BASE_DIR, 'files', 'es'))
        if request_data.get('request_methods') == 'get':
            try:
                rst = client.get(index=request_data.get('es_index'), doc_type='_all', # doc_type 有detail和_all, 也可以自定义
                                 id=request_data.get('es_document_id'))
                try:
                    with open(file=json_file, mode='a', encoding='utf-8') as fp:
                        fp.write(str(json.dumps(rst, ensure_ascii=False, indent=2)))
                except IOError:
                    logger.error('生成文件异常：%s' % str(traceback.format_exc()))
                data = {
                    'data': rst,
                    'errcode': 0,
                    'file': 'http://owa.srv.pigs.com/download/files/es/' + file_name
                }
                return JsonResponse(data=data)
            except NotFoundError:
                logger.warning('文档id不存在:%s' %str(traceback.format_exc()))
                return JsonResponse(data={'errcode': 404, 'msg': '文档id不存在！'})
            except BaseException as e:
                logger.error('请求异常，%s' %(str(traceback.format_exc())), e)
                return JsonResponse(data={'errcode': 500, 'msg': '请求异常,请稍后再试！'})

        elif request_data.get('request_methods') == 'post':
            try:
                rst = client.search(index=request_data.get('es_index'), body=request_data.get('request_body'))
                try:
                    with open(file=json_file, mode='a', encoding='utf-8') as fp:
                        fp.write(str(json.dumps(rst, ensure_ascii=False, indent=2)))
                except IOError:
                    logger.error('生成文件异常：%s' % str(traceback.format_exc()))
                data = {
                    'data': rst,
                    'errcode': 0,
                    'file': 'http://owa.srv.pigs.com/download/files/es/' + file_name
                }
                return JsonResponse(data=data)
            except BaseException as e:
                logger.error('请求异常，%s' %(str(traceback.format_exc())), e)
                return JsonResponse(data={'errcode': 500, 'msg': '请求异常,请稍后再试！'})
        else:
            return JsonResponse(data={'errcode': 403, 'msg': '请求的方法不允许！'})
