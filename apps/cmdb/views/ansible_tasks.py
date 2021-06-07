#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
@Time: 2021/4/29 0029 下午 3:19
@Author: micheng. <safemonitor@outlook.com>
@File: ansible_tasks.py
"""

import datetime
import logging
import os
import re
import sys
import traceback
import uuid
from datetime import datetime as dt

from django.db.models import Q
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from celery.result import AsyncResult

from devops_api.settings import BASE_DIR
from tasks.ansible_cmd import command_shell, check_celery_status, ansible_sendfile_celery_status, playbook_command
from apps.cmdb.models import Server, EcsAuthSSH, AnsibleExecHistory, AnsibleSyncFile, AnsibleExecTemplate
from apps.cmdb.serializers.server import ExecuteTaskServerSerializer
# from controller.ansible.runner import AdHocRunner, get_default_options, Options, PlayBookRunner
# from controller.ansible.inventory import BaseInventory
from controller.ansible.mongo_logs import Mongodb
from utils.authorization import MyAuthentication
from utils.code import RandCode
from utils.csrf_disable import CsrfExemptSessionAuthentication
from utils.pagination import MyPageNumberPagination
from utils.http_response import APIResponse
from utils.permissions import MyPermission
from utils.time_utils import datetime2str_by_format

sys.path.insert(0, "../..")
logger = logging.getLogger('default')


class ExecuteTaskServerList(ListAPIView):

    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    # queryset = Server.objects.all()
    serializer_class = ExecuteTaskServerSerializer
    pagination_class = MyPageNumberPagination

    def get_queryset(self):
        """Filter active products."""
        return Server.objects.all()


class SearchHostView(ListAPIView):

    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        keyword = request.GET.get('host', None)
        if keyword is not None:
            keyword = keyword.strip()
            host_obj = Server.objects.filter(
                Q(instance_id=keyword) | Q(private_ip=keyword) | Q(public_ip=keyword) | Q(hostname__icontains=keyword))
            paginator = MyPageNumberPagination()
            host = paginator.paginate_queryset(host_obj, self.request, view=self)
            print(host)
            serializer = ExecuteTaskServerSerializer(host, many=True)
            print(serializer.data)
            return Response(serializer.data)


class ExecuteTaskView(APIView):

    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        data = request.query_params
        ret = Mongodb().filter(task_id=data.get('task_id'))
        if not ret:
            return APIResponse(errcode=404, errmsg='未找到执行记录！')
        return APIResponse(data=ret)

    def post(self, request, *args, **kwargs):
        """
        执行ansible任务
        """
        data = request.data['params']
        logger.info("任务执行参数={%s}" % str(data))
        """
        host_data = [
            {
                "hostname": "testserver",
                "ip": "192.168.1.35",
                "port": 22,
                "username": "root",
                "password": "xxxxx.",
                "become": {
                    "method": "su",  # su , sudo
                    "user": "root",  # 默认以root用户执行
                    # "pass": "123456",
                },
            },
        ]
        """
        host_data = []

        server_obj = EcsAuthSSH.objects.filter(server_type='linux').first()
        if server_obj is None:
            logger.warning("请在密码表中配置linux远程用户和密码")
            return APIResponse(errcode=404, errmsg='请配置linux远程用户和密码')

        for host in data['hostList']:
            tmp = {}
            logger.info('执行主机：{}, 主机ip: {}'.format(str(host.get('instance_id')), str(host.get('private_ip'))))
            tmp['hostname'] = host.get('instance_id')
            tmp['ip'] = host.get('private_ip')
            tmp['become'] = {}
            tmp['become']['method'] = 'sudo'
            tmp['become']['user'] = data.get('cmdUser', 'root')
            tmp['username'] = server_obj.username
            tmp['password'] = server_obj.password
            tmp['port'] = server_obj.port
            host_data.append(tmp)

        # 任务超时时间
        timeout = 60 if data.get('cmdTimeout') == '' or data.get('cmdTimeout') is None else int(data.get('cmdTimeout'))
        logger.info('任务执行超时时间：%s' % timeout)

        if int(data.get('cmdSourceValue')) == 2 and int(data.get('cmdTypeValue')) == 5:
            # 执行Playbook yaml
            playbook_id = int(data.get('cmdTemplate'))
            template_obj = AnsibleExecTemplate.objects.filter(id=playbook_id).first()
            if not template_obj:
                return APIResponse(errcode=404, errmsg='模板文件不存在！')

            options = {
                'timeout': timeout,
                'passwords': '',
                'playbook_path': template_obj.template_dir
            }
            command_id = RandCode().uuid4_int()
            print(host_data, options, command_id)
            job_id = playbook_command.delay(host_data=host_data, options=options, job_id=command_id)
            job_status = AsyncResult(str(job_id))
            print("Celery任务id是: %s, 任务状态：%s" % (job_id, job_status.state))
            check_celery_status.delay(str(job_id))
            try:
                history_data = {
                    'job_name': data.get('taskName'),
                    'job_id': job_id,
                    'job_status': job_status.state,
                    'command_id': command_id,
                    'command_type': 'PlayBook',
                    'execute_user': data.get('cmdUser') if data.get('cmdUser') else 'root',
                    'host_count': len(host_data),
                    'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'command_content': 'Template PlayBook'
                }
                AnsibleExecHistory.objects.create(**history_data)

            except BaseException as e:
                print(traceback.format_exc())
                print("出错了: %s" % str(e))
                return APIResponse(errcode=9999, errmsg=str(e))

            return APIResponse(data={'msg': '任务下发成功！'})

        elif int(data.get('cmdSourceValue')) == 1 and int(data.get('cmdTypeValue')) == 3:
            # 执行Shell 命令
            # 异步任务 需要传递 task_time 任务所执行的时间， async = 前端的task_time 180
            # poll 0
            # 在yaml playbook 中执行异步任务
            """"
            tasks:
            - shell: sleep 10; hostname -i
              async: 10 # 异步
              poll: 0
    
            """
            tasks = []
            global command, command_lines
            try:
                command_lines = data.get('commandData', None)
                if command_lines is None or command_lines == '':
                    return APIResponse(errcode=404, errmsg='执行命令不能为空')
                command_list = str(command_lines).split('\n')
                logger.info("命令列表：%s" % str(command_list))
                for command_line in range(len(command_list)):
                    """对多个命令进行拆分"""
                    command = {"action": {"module": "shell", "args": None}, "name": data.get('taskName')}

                    if command_list[command_line] is None or command_list[command_line] == '':
                        pass
                        # del command_list[command_line]
                    else:
                        command['action']['args'] = command_list[command_line]
                        tasks.append(command)
            except Exception as e:
                print(e)
                command['action']['args'] = command_lines
                # tasks = [{"action": {"module": "shell", "args": data.get('commandData')}, "name": data.get(
                # 'taskName')},]
            logger.info(tasks)
            command_id = RandCode().uuid4_int()
            options = {'timeout': timeout}

            job_id = command_shell.delay(host_data, options, tasks, command_id)
            job_status = AsyncResult(str(job_id))
            print("Celery任务id是: %s, 任务状态：%s" % (job_id, job_status.state))
            check_celery_status.delay(str(job_id))
            # print("result---", job_status.result)
            # print("status---", job_status.status)
            # print("state---", job_status.state)
            # from utils.async_job_result import CeleryAsyncResult
            # CeleryAsyncResult(str(job_id)).get_celery_result()
            # 63f33395-0289-428a-a0ac-46f05f9bd318
            try:
                history_data = {
                    'job_name': data.get('taskName'),
                    'job_id': job_id,
                    'job_status': job_status.state,
                    'command_id': command_id,
                    'command_type': 'Shell',
                    'execute_user': data.get('cmdUser') if data.get('cmdUser') else 'root',
                    'host_count': len(host_data),
                    'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'command_content': command_lines
                }
                AnsibleExecHistory.objects.create(**history_data)
                # inventory = BaseInventory(host_data)
                # runner = AdHocRunner(inventory=inventory, options=options)
                # runner.run(tasks, "all", execution_id=str(job_id))
                # print(ret.results_summary)
                # print(ret.results_raw)
            except BaseException as e:
                print(traceback.format_exc())
                print("出错了: %s" % str(e))
                return APIResponse(errcode=9999, errmsg=str(e))

            return APIResponse(data={'msg': '任务下发成功！'})

        else:
            '''
            执行windows 主机命令
            '''
            # host_data = [
            #     {'hostname': 'i-bp10rydhf43t7r07v8wf', 'ip': 'xxxxxx',
            #      'username': 'administrator', 'password': 'xxxxx', 'port': 5985},
            # ]
            host_data = []
            server_obj = EcsAuthSSH.objects.filter(server_type='windows').first()
            if server_obj is None:
                logger.warning("请在密码表中配置windows远程用户和密码")
                return APIResponse(errcode=404, errmsg='请配置windows远程用户和密码')

            for host in data['hostList']:
                tmp = {}
                logger.info('执行主机：{}, 主机ip: {}'.format(str(host.get('instance_id')), str(host.get('private_ip'))))
                tmp['hostname'] = host.get('instance_id')
                tmp['ip'] = host.get('private_ip')
                tmp['username'] = server_obj.username
                tmp['password'] = server_obj.password
                tmp['port'] = 5985
                host_data.append(tmp)
            print(host_data)
            # inventory = BaseInventory(host_data)
            # Options.connection = 'winrm'
            # runner = AdHocRunner(inventory, options=Options)
            # tasks = [
            #     {"action": {"module": "script", "args": 'C:\\Users\\Administrator\\Desktop\\test.ps1'},
            #      "name": "run_whoami"},
            # ]
            tasks = []
            command = {"action": {"module": "win_command", "args": None}, "name": data.get('taskName')}
            command_lines = None
            try:
                command_lines = data.get('commandData', None)
                if command_lines is None or command_lines == '':
                    return APIResponse(errcode=404, errmsg='执行命令不能为空')
                command_list = str(command_lines).split('\n')
                logger.info("命令列表：%s" % str(command_list))
                for command_line in range(len(command_list)):
                    """对多个命令进行拆分"""
                    command = {"action": {"module": "win_command", "args": None}, "name": data.get('taskName')}

                    if command_list[command_line] is None or command_list[command_line] == '':
                        pass
                    else:
                        command['action']['args'] = command_list[command_line]
                        tasks.append(command)
            except Exception as e:
                print(e)
                command['action']['args'] = command_lines
            logger.info(tasks)
            command_id = RandCode().uuid4_int()
            options = {'timeout': timeout, 'connection': 'winrm'}
            job_id = command_shell.delay(host_data, options, tasks, command_id)
            job_status = AsyncResult(str(job_id))
            print("Celery任务id是: %s, 任务状态：%s" % (job_id, job_status.state))
            check_celery_status.delay(str(job_id))
            try:
                history_data = {
                    'job_name': data.get('taskName'),
                    'job_id': job_id,
                    'job_status': job_status.state,
                    'command_id': command_id,
                    'command_type': 'PowerShell',
                    'execute_user': data.get('cmdUser') if data.get('cmdUser') else 'administrator',
                    'host_count': len(host_data),
                    'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'command_content': command_lines
                }
                AnsibleExecHistory.objects.create(**history_data)
            except BaseException as e:
                print(traceback.format_exc())
                print("出错了: %s" % str(e))
                return APIResponse(errcode=9999, errmsg=str(e))

            return APIResponse(data={'msg': '任务下发成功！'})


class TasksExecList(APIView):

    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        """
        获取Ansible 执行历史记录
        """
        try:
            history_ojb = AnsibleExecHistory.objects.all().values()
            return APIResponse(data=history_ojb)
        except TypeError as e:
            print(e)
            pass

        return APIResponse(data={})

    def post(self, request, *args, **kwargs):
        """
        获取Ansible 单个命令 执行历史记录
        """
        data = request.data
        command_id = data.get('command_id')
        status = data.get('status', None)
        ret = Mongodb().filter(task_id=command_id, status=status)
        if not ret:
            return APIResponse(errcode=404, errmsg='未找到执行记录！')

        return APIResponse(data=ret)


class UploadFile(APIView):

    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission]

    def post(self, request, *args, **kwargs):
        """
        上传文件接口
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            file_name = request.FILES.get('file', None)
            # 上传文件类型过滤
            file_type = re.match(r'.*\.(zip|tar.gz)', file_name.name)
            if not file_type:
                return APIResponse(errcode=10019, errmsg='文件类型不匹配(zip, tar.gz), 请重新上传')

            # 将上传的文件逐行读取保存到list中
            content = []
            upload_file_save_directory = 'ansible_upload_file_tmp'

            for line in file_name.read().splitlines():
                content.append(line)

            my_custom_date = dt.now()
            directory_time = my_custom_date.strftime('%Y-%m-%d')
            files_uuid = uuid.uuid1()
            # 获取文件扩展名及文件名称
            file_ext_name = file_name.name.split('.')[-1]

            if not os.path.exists(os.path.join(BASE_DIR, upload_file_save_directory, directory_time)):
                os.makedirs(os.path.join(BASE_DIR, upload_file_save_directory, directory_time))

            save_files = open(os.path.join(BASE_DIR, upload_file_save_directory, directory_time,
                                           str(files_uuid) + ".%s" % file_ext_name), 'wb+')
            for chunk in file_name.chunks():  # 分块写入文件
                save_files.write(chunk)
            save_files.close()

            data = {
                'file_name': "%s.%s" % (str(files_uuid), file_ext_name),
                'file_dir': os.path.join(BASE_DIR, upload_file_save_directory, directory_time,
                                         str(files_uuid) + ".%s" % file_ext_name)
            }
            logger.info("%s文件上传成功, 上传人:" % (file_name,))
            return APIResponse(data=data)

        except Exception as e:
            logger.error("文件上传失败, 失败原因: %s, %s" % (str(e), str(traceback.format_exc())))
            return APIResponse(errcode=10020, errmsg='服务器内部错误', status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SendFileView(APIView):

    authentication_classes = [MyAuthentication, ]
    permission_classes = [MyPermission, ]

    def post(self, request, *args, **kwargs):
        """
        Ansible 文件分发接口
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        data = request.data['params']
        logger.info("文件分发任务执行参数={%s}" % str(data))
        host_data = []
        server_obj = EcsAuthSSH.objects.filter(server_type='linux').first()
        if server_obj is None:
            logger.warning("请在密码表中配置linux远程用户和密码")
            return APIResponse(errcode=404, errmsg='请配置linux远程用户和密码')
        # 任务超时时间
        timeout = 60 if data.get('cmdTimeout') == '' or data.get('cmdTimeout') is None else int(
            data.get('cmdTimeout'))
        logger.info('文件任务执行超时时间：%s' % timeout)

        for host in data['hostList']:
            tmp = {}
            logger.info('文件分发执行主机：{}, 主机ip: {}'.format(str(host.get('instance_id')), str(host.get('private_ip'))))
            tmp['hostname'] = host.get('instance_id')
            tmp['ip'] = host.get('private_ip')
            tmp['become'] = {}
            tmp['become']['method'] = 'sudo'
            tmp['become']['user'] = data.get('cmdUser', 'root')
            tmp['username'] = server_obj.username
            tmp['password'] = server_obj.password
            tmp['port'] = server_obj.port
            host_data.append(tmp)
        src_dir = data.get('uploadFile')
        dst_dir = data.get('fileDst')
        dst_file = data.get('fileName')
        tasks = [
            {"action": {"module": "copy", "args": {"src": src_dir, "dest": dst_dir + '/' + dst_file, "force": True}},
             "name": '文件分发'}]
        command_id = RandCode().uuid4_int()
        options = {'timeout': timeout}
        job_id = command_shell.delay(host_data, options, tasks, command_id)
        job_status = AsyncResult(str(job_id))
        print("Celery任务id是: %s, 任务状态：%s" % (job_id, job_status.state))
        ansible_sendfile_celery_status.delay(str(job_id))
        try:
            history_data = {
                'job_id': job_id,
                'job_status': job_status.state,
                'command_id': command_id,
                'execute_user': data.get('cmdUser') if data.get('cmdUser') else 'root',
                'host_count': len(host_data),
                'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'dst_dir': data.get('fileDst'),
                'dst_filename': data.get('fileName'),
                'src_filename': data.get('uploadFile')
            }
            AnsibleSyncFile.objects.create(**history_data)
        except BaseException as e:
            print(traceback.format_exc())
            print("出错了: %s" % str(e))
            return APIResponse(errcode=9999, errmsg=str(e))

        return APIResponse(data={'msg': '任务下发成功！'})


class SendFileList(APIView):

    authentication_classes = [MyAuthentication, ]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        """
        获取Ansible 执行历史记录
        """
        try:
            history_ojb = AnsibleSyncFile.objects.all().values()
            return APIResponse(data=history_ojb)
        except TypeError as e:
            print(e)
            pass

        return APIResponse(data={})

    def post(self, request, *args, **kwargs):
        """
        获取Ansible 单个命令 执行历史记录
        """
        data = request.data
        job_id = data.get('job_id')
        status = data.get('status', None)
        ret = Mongodb().filter(task_id=job_id, status=status)
        if not ret:
            return APIResponse(errcode=404, errmsg='未找到执行记录！')
        return APIResponse(data=ret)


class AnsibleTemplateView(APIView):

    authentication_classes = [MyAuthentication, ]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        """
        获取Ansible Template List
        """
        try:
            template_list = AnsibleExecTemplate.objects.all().values()
            return APIResponse(data=template_list)
        except TypeError as e:
            print(e)
            pass

        return APIResponse(data={})

    def post(self, request, *args, **kwargs):
        """
        创建Ansible Template
        """
        data = request.data
        now = datetime.datetime.now()
        time = datetime2str_by_format(now)
        try:
            obj = {
                'template_name': data.get('name'),
                'template_dsc': data.get('desc'),
                'command_type': 'playbook',
                'template_dir': data.get('templateDir'),
                'created_at': time
            }
            AnsibleExecTemplate.objects.create(**obj)
            return APIResponse(data={'msg': '模板创建成功'})
        except Exception as e:
            print(e)
            logger.error(traceback)
            return APIResponse(errcode=10044, errmsg='模板创建失败')

    def delete(self, request, *args, **kwargs):
        """
        删除Ansible Template
        """
        data = request.query_params
        template_id = data.get('id', None)
        print(data, template_id)
        if template_id is None or template_id == '':
            return APIResponse(errcode=404, errmsg='模板文件不存在')
        try:
            AnsibleExecTemplate.objects.filter(id=template_id).delete()
            return APIResponse(data={'msg': '模板删除成功'})
        except Exception as e:
            print(e)
            logger.error(traceback)
            return APIResponse(errcode=10044, errmsg='模板删除失败')


class AnsibleTemplateReadView(APIView):

    authentication_classes = [MyAuthentication, ]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        data = request.query_params
        ret = AnsibleExecTemplate.objects.filter(id=data.get('id')).first()
        try:
            with open(file=ret.template_dir, mode='r', encoding='utf-8') as fp:
                file_ojb = fp.read()
                return APIResponse(data=file_ojb)
        except FileNotFoundError:
            return APIResponse(errcode=404, errmsg='模板文件不存在！')


class TemplateSearch(APIView):

    authentication_classes = [MyAuthentication, ]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        """
        模板搜索
        """
        data = request.query_params['keyword']
        if not data:
            query_set = AnsibleExecTemplate.objects.all().values()
        else:
            query_set = AnsibleExecTemplate.objects.filter(
                Q(template_name__icontains=data) | Q(template_dsc__icontains=data) | Q(
                    template_dir__icontains=data)).values()

        return APIResponse(data=query_set)


class CommandSearch(APIView):

    authentication_classes = [MyAuthentication, ]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        """
        执行命令搜索
        """
        data = request.query_params['keyword']
        if not data:
            query_set = AnsibleExecHistory.objects.all().values()
        else:
            query_set = AnsibleExecHistory.objects.filter(
                Q(command_id__icontains=data) | Q(job_name__icontains=data) | Q(command_type__icontains=data)).values()

        return APIResponse(data=query_set)


class SendFileSearch(APIView):

    authentication_classes = [MyAuthentication, ]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        """
        文件分发历史搜索
        """
        data = request.query_params['keyword']

        if not data:
            query_set = AnsibleSyncFile.objects.all().values()
        else:
            query_set = AnsibleSyncFile.objects.filter(
                Q(command_id__icontains=data) | Q(dst_filename__icontains=data) | Q(dst_dir__icontains=data)).values()

        return APIResponse(data=query_set)

