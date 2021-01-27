#!/bin/env python3
# -*- coding: utf-8 -*-

"""
@Time: 2020/10/27 10:08
@Author: yu.jiang <safemonitor@outlook.com>
@License: Apache License
@File: deploy.py

"""
import datetime
import json
import re
import time
import traceback
import uuid
from decouple import config
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django_redis import get_redis_connection
from jenkinsapi.jenkins import Jenkins
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from api.models import Project, DeployTask, DeployLogs, BuildHistory, UserInfo
from api.utils.permissions import MyPermission
from utils.check_jenkins import JenkinsStauts
from api.utils.authorization import MyAuthentication
from utils.rest_page import StandardResultsSetPagination
from utils.serializer import ApprovalListSerializer
from api.tasks import check_status, deploy_send_dingtalk_work_notice, send_dingtalk_group
import logging
logger = logging.getLogger('default')
conn_redis = get_redis_connection('default')
local_time = time.strftime('%Y-%m-%d %H:%M:%S')


class DeployView(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def post(self, request, *args, **kwargs):
        """
        创建部署单
        :param request:
        :param args:
        :param kwargs:
        :return:
        """

        data = json.loads(request.body)
        file = data['params']['file']
        logger.info('原始请求报文: %s' % str(data))
        err_file_name = []
        for file_status in file:
            err_file_name.append(file_status['name']) if int(file_status['percent']) != 100 else print('\n')

        # 判断是否有未上传的文件
        if err_file_name:
            logger.warning('%s 未上传测试报告, 或上传的文件格式不正确！ 原因:%s' % (request.user.name, err_file_name))
            return JsonResponse(data={"errcode": -1, "msg": "未上传测试报告, 或上传的文件格式不正确！", "data": {"fileName": err_file_name}})
        elif file:
            # 应用部署单, 生成的参数为：
            # project_id: 应用编号, task_name: 任务id, submit_user: 部署发起人, submit_mobile: 提交人手机号
            project_id = data['params']['projectId']
            try:
                project_obj = Project.objects.filter(id=project_id).values('title', 'project_env','is_container').first()
                deploy_env = str(project_obj['project_env']).upper()
                task_id = str(uuid.uuid1()).replace('-', '')
                deploy_info = data['params']['deploy']
                title = deploy_info['title']
                version = deploy_info['version']
                desc = deploy_info['desc']
                develop_user = str(deploy_info['developUser']).strip().split(' ')
                online_time = deploy_info['onlineTime']
                # 将online_time （2020-11-17T08:25:56.812Z）转换为本地时间2017-07-28 16:28:47.776000
                UTC_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
                utc_time = datetime.datetime.strptime(online_time, UTC_FORMAT)
                online_local_time = utc_time + datetime.timedelta(hours=8)

                ding_talk = deploy_info['dingTalk']
                deploy_type = deploy_info['deployType']
                approval_user = deploy_info['approvalUser']
                # 原始文件名
                logger.info("原始文件名称：%s" % file)
                original_file_name = file[0]['name']
                test_repo = file[0]['response']['data']['url'].split('/files/')[1]
                # 获取审批人user_id
                obj = UserInfo.objects.filter(name=approval_user).first()
                # 0容器化应用, 1标准化应用
                if project_obj['is_container'] == 0 and deploy_type == 'CONTAINER':
                    with transaction.atomic():
                        DeployTask.objects.create(
                            task_id=task_id, project_id=project_id, title=title,
                            version=version, before_comment=desc, dingtalk_notice=ding_talk,
                            approval_user=approval_user, test_report=test_repo,develop_user=develop_user,
                            online_time=online_local_time, submit_people=request.user.name, submit_user_id=request.user.user_id,
                            deploy_env=deploy_env, deploy_type=deploy_type, original_file_name=original_file_name
                        )
                        logger.info('%s 发起的部署任务单创建成功, 应用类型:CONTAINER 任务ID:%s 发布的版本:%s' % (request.user.name, task_id, version))
                        # 将操作记录写入到deploy_logs表中
                        DeployLogs.objects.create(task_id=task_id, project_id=project_id, message='%s发起了部署单申请' % request.user.name)

                    try:
                        # 给审批人发送工作通知
                        data = {
                            'title': '有一条上线申请单待审批！',
                            'msg': f'####    请登陆运维平台审批该工单  \n【申请标题】  \n  {title}  \n  \n【上线版本】 \n  {version}  \n  \n【提交人员】  \n  {request.user.name}  \n  \n【开发人员】  \n  {develop_user}  \n {local_time}',
                            'user_id': str(obj.user_id)
                        }
                        deploy_send_dingtalk_work_notice.delay(data)

                    except BaseException as e:
                        logger.error('发送钉钉工作通知失败, 异常原因: %s' % str(traceback.format_exc()))

                    return JsonResponse(data={"errcode": 0, "msg": "部署单创建成功！", "data": "null"})

                elif project_obj['is_container'] == 1 and deploy_type == 'INC':
                    with transaction.atomic():
                        DeployTask.objects.create(
                            task_id=task_id, project_id=project_id, title=title, version=version, before_comment=desc,
                            dingtalk_notice=ding_talk, approval_user=approval_user, test_report=test_repo,
                            develop_user=develop_user,
                            online_time=online_local_time, submit_people=request.user.name, submit_user_id=request.user.user_id,
                            deploy_env=deploy_env, deploy_type=deploy_type, original_file_name=original_file_name
                        )

                        logger.info('%s 发起的部署任务单创建成功, 应用类型:INC 任务ID:%s 发布的版本:%s' % (request.user.name, task_id, version))
                        DeployLogs.objects.create(task_id=task_id, project_id=project_id,message='%s发起了部署单申请' % request.user.name)
                    try:
                        # 给审批人发送工作通知
                        data = {
                            'title': '有一条上线申请单待审批！',
                            'msg': f'####    请登陆运维平台审批该工单  \n【申请标题】  \n  {title}  \n  \n【上线版本】  \n  {version}  \n  \n【提交人员】  \n  {request.user.name}  \n  \n【开发人员】  \n  {develop_user}  \n  {local_time}',
                            'user_id': str(obj.user_id)
                        }
                        deploy_send_dingtalk_work_notice.delay(data)

                    except BaseException as e:
                        logger.error('发送钉钉工作通知失败, 异常原因: %s' % str(traceback.format_exc()))

                    return JsonResponse(data={"errcode": 0, "msg": "部署单创建成功！", "data": "null"})

                elif project_obj['is_container'] == 1 and deploy_type == 'FULL':
                    with transaction.atomic():
                        DeployTask.objects.create(
                            task_id=task_id, project_id=project_id, title=title, version=project_obj["title"], before_comment=desc,
                            dingtalk_notice=ding_talk, approval_user=approval_user, test_report=test_repo,
                            develop_user=develop_user,
                            online_time=online_local_time, submit_people=request.user.name, submit_user_id=request.user.user_id,
                            deploy_env=deploy_env, deploy_type=deploy_type, original_file_name=original_file_name
                        )
                        logger.info('%s 发起的部署任务单创建成功, 应用类型:FULL 任务ID:%s 发布的版本:%s' % (request.user.name, task_id, version))
                        DeployLogs.objects.create(task_id=task_id, project_id=project_id,message='%s发起了部署单申请' % request.user.name)
                    try:
                        # 给审批人发送工作通知
                        data = {
                            'title': '有一条上线申请单待审批！',
                            'msg': f'####    请登陆运维平台审批该工单  \n【申请标题】  \n  {title}  \n  \n【上线版本】  \n  {project_obj["title"]}  \n  \n【提交人员】  \n  {request.user.name}  \n  \n【开发人员】  \n  {develop_user}  \n  {local_time}',
                            'user_id': str(obj.user_id)
                        }
                        deploy_send_dingtalk_work_notice.delay(data)

                    except BaseException as e:
                        logger.error('发送钉钉工作通知失败, 异常原因: %s' % str(traceback.format_exc()))

                    return JsonResponse(data={"errcode": 0, "msg": "部署单创建成功！", "data": "null"})
                else:
                    logger.warning('%s 发布类型不正确' % request.user.name)
                    return JsonResponse(data={
                        "errcode": "10300",
                        "msg": "您选择的发布类型不正确, 请重新选择！",
                        "data": {"fileName": ''}
                    })

            except BaseException as e:
                logger.error('系统出现未知错误, 异常原因:%s' % str(traceback.format_exc()))
                return JsonResponse(data={
                    "errcode": "1006",
                    "msg": "系统异常, 请刷新重试!",
                    "data": e
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR, json_dumps_params={'ensure_ascii': False})

        else:
            logger.warning('%s 未上传测试报告, 或上传的文件格式不正确！ 原因:%s' % (request.user.name, err_file_name))
            return JsonResponse(data={"errcode": -1, "msg": "未上传测试报告, 或上传的文件格式不正确！", "data": {"fileName": err_file_name}})


class DeployDetailView(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def post(self, request, *args, **kwargs):
        """
        根据部署单id, 查询详细
        :param request:
        :param args: queryId=11
        :param kwargs:
        :return:
        """
        try:
            query_id = json.loads(request.body)['params']['queryId']
            if query_id is not None and query_id != '':
                query_deploy_id = DeployTask.objects.filter(pk=query_id).order_by('id')
                paginator = StandardResultsSetPagination()
                page_deploy_list = paginator.paginate_queryset(query_deploy_id, self.request, view=self)
                serializer_deploy_info = ApprovalListSerializer(page_deploy_list, many=True)
                page_deploy = paginator.get_paginated_response(serializer_deploy_info.data)
                return Response(page_deploy.data)

            logger.warning('部署单id不正确, 当前无法查看部署单详情')

        except BaseException as e:
            logger.error('用户:%s 请求部署单详情接口出现系统异常, 原因: %s' % request.user.name, str(traceback.format_exc()))
            return JsonResponse(data={
                "errcode": "1006",
                "msg": "系统异常, 请刷新重试!",
                "data": e
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR, json_dumps_params={'ensure_ascii': False})


class DeployAuditLogsView(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        """
        部署单审计日志
        :param request:
        :param args: task_id
        :param kwargs:
        :return:
        """

        task_id = request.GET.get('taskId', None)
        try:
            if task_id is not None:
                data = DeployLogs.objects.filter(task_id=task_id).values()
                data = list(data)
                return JsonResponse({"errcode": 0, "msg": "操作成功", "data": data}, json_dumps_params={'ensure_ascii': False})

            return JsonResponse(data={"errcode": "2006","msg": "获取详细失败","data": "null"}, json_dumps_params={'ensure_ascii': False})

        except BaseException as e:
            logger.error('接口异常, 原因: %s' % str(e))
            return JsonResponse(data={
                "errcode": "1006",
                "msg": "系统异常, 请刷新重试!",
                "data": e
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR, json_dumps_params={'ensure_ascii': False})


class ApprovalDeployStatus(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def post(self, request, *args, **kwargs):
        """
        审批部署任务单
        :param request:
        :param args:
        :param kwargs:
        :return:
        """

        data = json.loads(request.body)['params']
        try:
            obj = DeployTask.objects.filter(task_id=data['taskId'])
            # 判断当前用户是否为审批人
            if obj and request.user.is_superuser or str(request.user.name) == str(obj.first().approval_user):
                if data['status'] == "agree":
                    with transaction.atomic():
                        obj.update(status=2)
                        DeployLogs.objects.create(
                            task_id=data['taskId'],
                            project_id=obj.first().project_id,
                            message='%s已同意您发起的部署单, 等待部署中。 ' % request.user.name)
                        logger.info('%s发起的应用部署上线单已通过审核,&nbsp; 等待部署中, 任务ID: %s' % (str(obj.first().submit_people), data['taskId']))

                    try:
                        # 给审批人发送工作通知
                        is_dingtalk_notice = obj.first()
                        if is_dingtalk_notice.dingtalk_notice:
                            submit_user_id = UserInfo.objects.filter(name=is_dingtalk_notice.submit_people).first()
                            data = {
                                'title': '上线单已审批通过！',
                                'msg': f'\n【申请标题】  \n  {is_dingtalk_notice.title}  \n  \n【上线版本】  \n  \n  {is_dingtalk_notice.version}  \n  \n【开发人员】  \n  {is_dingtalk_notice.develop_user}  \n {local_time}',
                                'user_id': str(submit_user_id.user_id)
                            }
                            deploy_send_dingtalk_work_notice.delay(data)
                        # todo 通知运维
                        send_dingtalk_group.delay("%s \n 上线单已审批通过, 请前往运维平台部署" % str(obj.first().title))
                    except BaseException as e:
                        logger.error('发送钉钉群通知失败, 异常原因: %s' % str(traceback.format_exc()))

                    return JsonResponse(data={"errcode": 0, "msg": "操作成功", "data": "null"})

                elif data['status'] == "refuse":
                    if data['refuseMsg'] == '' or data['refuseMsg'] is None:
                        return JsonResponse(data={"errcode":3001, "msg": "拒绝原因不能为空", "data":"null"})
                    with transaction.atomic():
                        obj.update(status=6)
                        obj.update(refuse_msg=data['refuseMsg'])
                        DeployLogs.objects.create(
                            task_id=data['taskId'],
                            project_id=obj.first().project_id,
                            status=6,
                            message='%s已驳回您发起的部署单，原因: %s。 ' % (request.user.name, data['refuseMsg']))
                        logger.info('部署单: %s 已被%s拒绝' % (data['taskId'], str(request.user.name)))

                    try:
                        # 给审批人发送工作通知
                        is_dingtalk_notice = obj.first()
                        if is_dingtalk_notice.dingtalk_notice:
                            submit_user_id = UserInfo.objects.filter(name=is_dingtalk_notice.submit_people).first()
                            refuse_msg = data['refuseMsg']
                            data = {
                                'title': '上线单已被拒绝！',
                                'msg': f'#### 拒绝原因：{refuse_msg}  \n【申请标题】  \n  {is_dingtalk_notice.title}  \n  \n【上线版本】 \n  \n {is_dingtalk_notice.version}  \n  \n【开发人员】  \n  {is_dingtalk_notice.develop_user}  \n {local_time}',
                                'user_id': str(submit_user_id.user_id)
                            }
                            deploy_send_dingtalk_work_notice.delay(data)

                    except BaseException as e:
                        logger.error('发送钉钉工作通知失败, 异常原因: %s' % str(traceback.format_exc()))

                    return JsonResponse(data={"errcode": 0, "msg": "操作成功", "data": "null"})

                else:
                    logger.warning('非法操作, 参数异常')
                    return JsonResponse(data={"errcode":3001, "msg": "非法操作", "data":"null"})
            logger.info('您无权审批该工单, 操作人: %s' % str(request.user.name))
            return JsonResponse(data={"errcode": 3002, "msg": "非法操作, 您无权审批该工单！", "data": "null"})

        except BaseException as e:
            logger.error('系统出现异常, 原因: %s' % str(traceback.format_exc()))
            return JsonResponse(data={
                "errcode": "1006",
                "msg": "系统异常, 请刷新重试!",
                "data": e
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR, json_dumps_params={'ensure_ascii': False})


class DeployCode(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, IsAdminUser]

    def post(self, request, *args, **kwargs):
        """
        部署代码到服务器, 只允许管理员部署 (IsAdminUser)
        :param request:
        :param args:
        :param kwargs:
        :return:
        """

        data = json.loads(request.body)['params']
        task_id = data['taskId']
        global LOCK_PROJECT

        try:
            query_deploy_task = DeployTask.objects.filter(task_id=task_id).first()
            project_id = query_deploy_task.project_id
            query_project = Project.objects.filter(pk=project_id).first()
            project_name = query_project.title
            code_version = str(query_deploy_task.version).lower()
            deploy_type = query_deploy_task.deploy_type

            server = Jenkins(config('JENKINS_URL'), username=config('JENKINS_USER'), password=config('JENKINS_PASS'))
            build_history = BuildHistory()
            # 判断job是否存在， 0为容器化应用，1为普通应用
            if server.has_job(project_name):
                lock_value = conn_redis.get(project_name + "_lock")
                LOCK_PROJECT = project_name + "_lock"

                if lock_value is not None and lock_value.decode('utf-8') == "True":
                    logger.warning("上一个任务正在进行中, 请等待任务结束后再试. 操作人: %s" % request.user.name)
                    return JsonResponse(data={"errcode": 5001,"msg": "上一个任务正在进行中, 请稍后再试! ","data": "null"})
                else:
                    conn_redis.set(project_name + "_lock", 'True')
                    logger.info("没有获取到锁, 进行加锁{%s} 操作防止业务部署异常" % project_name)

                if query_deploy_task.deploy_type == "CONTAINER":
                    try:
                        # 截取版本号CONTAINER 正则提取1000
                        # version = re.findall('^CONTAINER_(?P<version>[0-9]+)', str(code_version).lower(), re.IGNORECASE)[0]
                        build_id = JenkinsStauts.jenkins_task_id(project_name)
                        server.build_job(project_name, params={'APP_NUMBER': code_version})
                        logger.info('%s开始部署应用: %s,  任务ID: %s, 版本: %s, 发布类型: %s' %(request.user.name, project_name, task_id, code_version, deploy_type))
                        query_deploy_task.status = 3
                        query_deploy_task.save()
                        # 写入操作日志表
                        DeployLogs.objects.create(
                            task_id=data['taskId'],
                            project_id=query_deploy_task.project_id,
                            status=3,
                            message='%s已开始部署应用 ' % (request.user.name))

                        # 插入构建记录到历史表
                        build_history.build_id = build_id
                        build_history.task_id = task_id
                        build_history.app_name = project_name
                        build_history.save()

                        async_result = check_status.delay(project_name, build_id, task_id)
                        logger.info('已开始部署应用, 异步任务返回ID: %s, 状态: %s' % (str(async_result.id), str(async_result.state)))
                        logger.info('项目部署大概需要5~15分钟, 稍后请注意钉钉通知, 应用名:%s, 版本号:%s' % (str(project_name), str(code_version)))
                        return JsonResponse(data={"errcode": 0,
                                                  "msg": "项目部署中,稍后请注意钉钉通知!",
                                                  "data": {"appliction": project_name, "version": code_version}})

                    except BaseException as e:
                        conn_redis.delete(LOCK_PROJECT)
                        logger.error('部署异常, 开始释放锁%s 异常原因: %s' % (LOCK_PROJECT,str(e)))
                        logger.error('部署异常, 异常原因: %s' % str(traceback.format_exc()))
                        # 写入操作日志表
                        DeployLogs.objects.create(
                            task_id=data['taskId'],
                            project_id=query_deploy_task.project_id,
                            status=5,
                            message='版本发布出现异常 ')

                        return JsonResponse(data={
                            "errcode": "4001",
                            "msg": "发布异常, 请联系运维处理!",
                            "data": e
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR, json_dumps_params={'ensure_ascii': False})

                elif  query_deploy_task.deploy_type == "INC":
                    lock = conn_redis.get(project_name + "_lock")
                    logger.info(f'获取锁{lock}，  部署类型INC')
                    if code_version.split('.')[-1] == "zip":
                        deploy_params = {
                            'Deploy': 'deploy',
                            'SLB': True,
                            'Inc_update': True,
                            'on_slb': True,
                            'svn_version': code_version
                        }
                        logger.info('%s开始部署应用: %s,  任务ID: %s, 版本: %s, 发布类型: %s' % (request.user.name, project_name, task_id, code_version, deploy_type))
                        build_id = JenkinsStauts.jenkins_task_id(project_name)
                        server.build_job(project_name, params=deploy_params)
                        query_deploy_task.status = 3
                        query_deploy_task.save()
                        # 写入操作日志表
                        DeployLogs.objects.create(
                            task_id=data['taskId'],
                            project_id=query_deploy_task.project_id,
                            status=6,
                            message='%s已开始部署应用 ' % (request.user.name))

                        # 插入构建记录到历史表
                        build_history.build_id = build_id
                        build_history.task_id = task_id
                        build_history.app_name = project_name
                        build_history.save()
                        async_result = check_status.delay(project_name, build_id, task_id)
                        logger.info('项目%s 构建状态异步任务返回ID: %s, 状态: %s' % (project_name, str(async_result.id), str(async_result.state)))
                        logger.info('项目增量部署中, 稍后请注意钉钉通知: %s' % str(deploy_params))
                        return JsonResponse(data={"msg": "项目部署中,稍后请注意钉钉通知", "errcode": 0})

                    else:
                        lock_value = conn_redis.delete(project_name + "_lock")
                        return JsonResponse(data={"errcode":404, "msg": "升级包格式不正确"})

                elif query_deploy_task.deploy_type == 'FULL':
                    # todo 构建common包
                    from api.utils.jenkins_trip_common import TripCommon
                    from api.tasks import check_trip_common_status
                    common_params = {
                        "AppName": project_name
                    }

                    common_package = "trip-common"
                    build_id = TripCommon.jenkins_task_id(common_package)
                    server.build_job(common_package, params=common_params)
                    query_deploy_task.status = 3
                    query_deploy_task.save()
                    # 写入操作日志表
                    DeployLogs.objects.create(
                        task_id=task_id,
                        project_id=query_deploy_task.project_id,
                        status=6,
                        message='正在拉取基础包，此过程可能耗时较长。')

                    # 插入构建记录到历史表
                    build_history.build_id = build_id
                    build_history.task_id = task_id
                    build_history.app_name = common_package
                    build_history.save()
                    check_trip_common_status.delay(common_package, build_id, task_id, request.user.name, deploy_type, project_name)
                    return JsonResponse(data={"msg": "项目全量部署中,稍后请注意钉钉通知", "errcode": 0})

                else:
                    lock_value = conn_redis.delete(project_name + "_lock")
                    logger.info('发布类型不支持, 允许的范围(INC, CONTAINER)')
                    return JsonResponse(data={
                        "errcode": "4003",
                        "msg": "不支持的操作, 请联系运维处理!",
                        "data": "null"
                    })

            else:
                logger.error('%s项目不存在, 请前往Jenkins配置' % (project_name))
                return JsonResponse(data={
                    "errcode": "4004",
                    "msg": "项目不存在,请联系运维添加项目！",
                    "data": "null"
                })

        except BaseException as e:
            conn_redis.delete(LOCK_PROJECT)
            logger.error('系统出现未知的错误, 开始释放锁%s 原因: %s' % (LOCK_PROJECT, str(e)))
            logger.error('系统出现未知的错误, 异常原因: %s' % str(traceback.format_exc()))
            return JsonResponse(data={
                "errcode": "1006",
                "msg": "系统异常, 请刷新重试!",
                "data": e
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR, json_dumps_params={'ensure_ascii': False})
