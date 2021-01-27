#!/bin/env python3
# -*- coding: utf-8 -*-

"""
@Time: 2020/11/1 18:51
@Author: yu.jiang <safemonitor@outlook.com>
@License: Apache License
@File: rollback.py

"""
import json
import time
import traceback
from decouple import config
from django.http import JsonResponse
from django_redis import get_redis_connection
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from api.models import Project, DeployRollBack
from api.utils.permissions import MyPermission
from utils.check_jenkins import JenkinsStauts
from api.utils.authorization import MyAuthentication
from utils.serializer import DeployRollBackModelSerializers
from jenkinsapi.jenkins import Jenkins
from api.tasks import rollback_sync_code_job_cluster, check_rollback_status
import logging
logger = logging.getLogger('default')
conn_redis = get_redis_connection('default')
local_time = time.strftime('%Y-%m-%d %H:%M:%S')


class DeployRollBackView(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        """
        列出最近5个可回滚的版本
        :param request:
        :param args: project 项目名, project_type 项目类型
        :param kwargs:
        :return:
        """

        rollback_id = request.GET.get('id', None)
        try:
            if rollback_id is not None:
                project_name = Project.objects.filter(pk=rollback_id).first()
                obj = DeployRollBack.objects.filter(project_name=project_name.title).order_by('-id')[:5]
                if obj.count() != 0:
                    ser = DeployRollBackModelSerializers(instance=obj, many=True, context={'request': request})
                    return JsonResponse({"errcode": 0, "msg": "success", "data": ser.data})

                return JsonResponse({"errcode": -1, "msg": "没有可回退的版本", "data": []},json_dumps_params={'ensure_ascii': False})

        except BaseException as e:
            logger.error('没有可回退的版本, 异常原因: %s' % str(traceback.format_exc()))
            return JsonResponse({"errcode": 404, "msg": "没有可回退的版本", "data": "null"}, json_dumps_params={'ensure_ascii': False})

    def post(self, request, *args , **kwargs):
        """
        创建部署回滚任务
        :param request:
        :param args: {'id': 1}
        :param kwargs:
        :return:
        """

        if not request.user.is_superuser:
            return JsonResponse({
                "errcode": 403,
                "msg": "您当前无权操作！",
                "data": []},json_dumps_params={'ensure_ascii': False})

        data = json.loads(request.body)['params']
        project_name = data['project_name']
        package_name = data['package_name']
        backup_type = data['backup_type']
        namespace = data['namespace']
        server = Jenkins(config('JENKINS_URL'), username=config('JENKINS_USER'), password=config('JENKINS_PASS'))
        if backup_type == "增量更新"  or backup_type == "全量更新":
            lock = conn_redis.get(project_name + "_lock")
            logger.info("获取任务锁: %s" % lock)
            if lock is not None and lock.decode('utf-8') == "True":
                logger.info("有其他任务正在进行中, 请稍后再试! {%s}" % project_name)
                return JsonResponse(data={"msg": "有其他任务正在进行中, 请稍后再试!", "errcode": -1})

            else:
                try:
                    deploy_params = {
                        'Deploy': 'rollback',
                        'SLB': True,
                        'Inc_update': False,
                        'on_slb': True,
                        'rollback_version': package_name
                    }
                    logger.info('开始回滚项目: %s, 版本: %s,  操作人: %s' % (project_name, package_name, request.user.name))
                    build_id = JenkinsStauts.jenkins_task_id(project_name)
                    server.build_job(project_name, params=deploy_params)
                    # todo 写入回滚日志表
                    async_result = check_rollback_status.delay(project_name, build_id)

                    logger.info('回滚的项目:%s 构建状态异步任务返回ID: %s, 状态: %s' % (project_name, str(async_result.id), str(async_result.state)))
                    logger.info('回滚的项目正在部署中, 稍后请注意钉钉通知: %s' % str(deploy_params))
                    return JsonResponse(data={"msg": "项目版本回退中, 稍后请注意钉钉通知", "errcode": 0})

                except BaseException as e:
                    logger.error('回滚失败, 请及时检查失败原因 %s' % str(traceback.format_exc()))
        else:
            lock = conn_redis.get(project_name + "_lock")
            logger.info("获取任务锁: %s" % lock)
            if lock is not None and lock.decode('utf-8') == "True":
                logger.info("有其他任务正在进行中, 请稍后再试! {%s}" % project_name)
                return JsonResponse(data={"msg": "有其他任务正在进行中, 请稍后再试!", "errcode": -1})

            else:
                if project_name is not None and package_name is not None and namespace is not None:
                    try:
                        # 加锁，回滚历史版本
                        logger.info('开始回滚项目: %s, 版本: %s,  操作人: %s' % (project_name, package_name, request.user.name))
                        conn_redis.set(project_name + "_lock", 'True')
                        logger.info('回滚操作已加锁，等待下一步操作')
                        # todo 调用kubernetes api接口, 对deloyment回滚
                        logger.info("开始回滚项目：%s, 命名空间：%s, 镜像版本：%s" %(project_name, namespace, data['registry']))
                        from api.utils.k8s_deployment_rollback import KubernetesApi
                        deployment_rollback_status = KubernetesApi.update_deployment(project_name, namespace, data['registry'])
                        if deployment_rollback_status.get('errcode') != 0:
                            return JsonResponse({
                                "errcode": 500,
                                "msg": "回滚异常", "data": []}, json_dumps_params={'ensure_ascii': False})

                        return JsonResponse({
                            "errcode": 0,
                            "msg": "回滚任务已开始，稍后请注意钉钉通知", "data": []},json_dumps_params={'ensure_ascii': False})

                    except BaseException as e:
                        logger.error('回滚失败, 请及时检查失败原因 %s' % str(traceback.format_exc()))

                return JsonResponse(data={
                    "errcode": 404,
                    "msg": "回滚版本信息出错, 或namespace未关联应用！",
                    "data": "null"
                })


class CreateDeployBackupView(APIView):
    authentication_classes =[]
    permission_classes = []

    def post(self, request, *args, **kwargs):
        """
        创建备份, 只允许jenkins机器访问该接口
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        allow_host_ip = config('BACKUP_ALLOW_HOST').split(',')
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        logger.info('获取的ip是：%s' % x_forwarded_for)
        if x_forwarded_for:
            client_ip = x_forwarded_for.split(',')[0]
        else:
            client_ip = request.META.get('REMOTE_ADDR')

        if client_ip in allow_host_ip:
            try:
                data = json.loads(request.body, encoding='utf-8')
                print(data, 11)
                orm_data = DeployRollBack.objects.create(**data)
                logger.info(f'数据备份成功: data={request.body}')
                return JsonResponse(data={'errcode': 0, 'msg': '备份成功'}, json_dumps_params={'ensure_ascii': False})

            except BaseException as e:
                logger.error(f'备份失败，{request.body}')
                logger.error('备份失败, 异常原因: %s' % str(traceback.format_exc()))
                return JsonResponse(data={'errcode': 500, 'msg': '备份异常'}, json_dumps_params={'ensure_ascii': False})
        else:
            return JsonResponse(data={
                'errcode': 403,
                'msg': '备份异常, 当前IP未被授权!'}, json_dumps_params={'ensure_ascii': False})