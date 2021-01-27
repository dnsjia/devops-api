#!/bin/env python3
# -*- coding: utf-8 -*-

"""
@Time: 2020/10/26 16:43
@Author: yu.jiang <safemonitor@outlook.com>
@License: Apache License
@File: upload.py

"""
import os
import re
import time
import traceback
import uuid
from datetime import datetime
from django.http import JsonResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from devops.settings import BASE_DIR
from utils.csrf_disable import CsrfExemptSessionAuthentication
import logging
logger = logging.getLogger('default')


class UploadView(APIView):
    # todo 文件上传校验登录用户
    permission_classes = []
    authentication_classes = [CsrfExemptSessionAuthentication, ]

    def post(self, request, *args, **kwargs):
        """
        上传测试报告接口
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        response = {}
        try:
            test_repo_name = request.FILES.get('file', None)
            # 上传文件类型过滤
            file_type = re.match(r'.*\.(doc|docx|zip|jpeg|png|jpg|tar.gz|rar)', test_repo_name.name)
            if not file_type:
                response['errcode'] = 10019
                response['msg'] = '文件类型不匹配(doc,docx,zip,jpg,png), 请重新上传'
                response['data'] = 'null'
                response['status'] = 'error'
                return JsonResponse(data=response)

            # 将上传的文件逐行读取保存到list中
            file_info = {}
            content = []
            for line in test_repo_name.read().splitlines():
                content.append(line)

            my_custom_date = datetime.now()
            directory_time = my_custom_date.strftime('%Y-%m-%d')
            files_uuid = uuid.uuid1()
            # 获取文件扩展名及文件名称
            file_ext_name = test_repo_name.name.split('.')[-1]
            file_info['name'] = "%s.%s" % (str(files_uuid), file_ext_name)

            if not os.path.exists(os.path.join(BASE_DIR, 'files', directory_time)):
                os.makedirs(os.path.join(BASE_DIR, 'files', directory_time))

            save_files = open(os.path.join(BASE_DIR, "files", directory_time, str(files_uuid) + ".%s" % file_ext_name), 'wb+')
            for chunk in test_repo_name.chunks():  # 分块写入文件
                save_files.write(chunk)
            save_files.close()

            # 上传文件的时间
            time_stamp = time.time()
            now = int(round(time_stamp * 1000))
            file_info['date'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now / 1000))
            file_info['url'] = "http://192.168.1.234:8000/files/%s/%s.%s" % (directory_time, str(files_uuid), file_ext_name)
            # 返回状态信息
            response['msg'] = "文件上传成功!"
            response['errcode'] = 0
            response['data'] = file_info
            print(file_info)
            #logger.info("%s文件上传成功, 上传人: %s" % (test_repo_name, request.user.name))
            logger.info("%s文件上传成功, 上传人:" % (test_repo_name))
            return JsonResponse(data=response)

        except Exception as e:
            logger.error("文件上传失败, 失败原因: %s" % str(traceback.format_exc()))
            response['msg'] = '服务器内部错误'
            response['errcode'] = 10020
            response['data'] = str(e)
            return JsonResponse(data=response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CaseUploadView(APIView):
    # todo 文件上传校验登录用户
    permission_classes = []
    authentication_classes = [CsrfExemptSessionAuthentication, ]

    def post(self, request, *args, **kwargs):
        """
        上传测试报告接口
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        response = {}
        try:
            test_repo_name = request.FILES.get('file', None)
            # 上传文件类型过滤
            file_type = re.match(r'.*\.(xlsx)', test_repo_name.name)
            if not file_type:
                response['errcode'] = 10019
                response['msg'] = '文件类型不匹配(xlsx), 请重新上传'
                response['data'] = 'null'
                response['status'] = 'error'
                return JsonResponse(data=response)

            # 将上传的文件逐行读取保存到list中
            file_info = {}
            content = []
            for line in test_repo_name.read().splitlines():
                content.append(line)

            my_custom_date = datetime.now()
            files_uuid = uuid.uuid1()
            # 获取文件扩展名及文件名称
            file_ext_name = test_repo_name.name.split('.')[-1]
            file_info['name'] = "%s.%s" % (str(files_uuid), file_ext_name)

            if not os.path.exists:
                os.makedirs(os.path.join(BASE_DIR, 'utils/case_action/excel_template'))

            save_files = open(os.path.join(BASE_DIR, "utils/case_action/excel_template", str(files_uuid) + ".%s" % file_ext_name), 'wb+')
            for chunk in test_repo_name.chunks():  # 分块写入文件
                save_files.write(chunk)
            save_files.close()

            # 上传文件的时间
            time_stamp = time.time()
            now = int(round(time_stamp * 1000))
            file_info['date'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now / 1000))
            file_info['url'] = "http://192.168.1.234:8000/utils/case_action/excel_template/%s.%s" % (str(files_uuid), file_ext_name)
            file_info['case_file'] = str(files_uuid) + ".%s" % file_ext_name
            # 返回状态信息
            response['msg'] = "文件上传成功!"
            response['errcode'] = 0
            response['data'] = file_info
            print(file_info)
            # logger.info("%s文件上传成功, 上传人: %s" % (test_repo_name, request.user.name))
            logger.info("%s文件上传成功, 上传人:" % (test_repo_name))
            return JsonResponse(data=response)

        except Exception as e:
            logger.error("文件上传失败, 失败原因: %s" % str(traceback.format_exc()))
            response['msg'] = '服务器内部错误'
            response['errcode'] = 10020
            response['data'] = str(e)
            return JsonResponse(data=response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)