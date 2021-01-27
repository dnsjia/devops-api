#!/bin/env python3
# -*- coding: utf-8 -*-

"""
@Time: 2020/11/23 14:02
@Author: yu.jiang <safemonitor@outlook.com>
@License: Apache License
@File: download.py

"""
from rest_framework.views import APIView
from django.http import FileResponse, HttpResponse
from pathlib import Path
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


class DownLoadFile(APIView):
    def get(self, request, *args, **kwargs):
        file_path = request.path.split('download')[1]
        ext = os.path.basename(file_path).split('.')[-1].lower()

        # 将第一个反斜杠替换为空 /files/es/chenyihao_20201123131458.json  files/es/chenyihao_20201123131458.json
        es_json_path = os.path.join(BASE_DIR, file_path.replace('/', '',1))

        # 允许下载的文件后缀名
        if ext in ['txt', 'json', 'xlsx']:
            response = FileResponse(open(es_json_path, 'rb'))
            response['content_type'] = "application/octet-stream"
            response['Content-Disposition'] = 'attachment;filename={}'.format(os.path.basename(es_json_path))
            return response

        print(BASE_DIR)
        return HttpResponse("hello world!")