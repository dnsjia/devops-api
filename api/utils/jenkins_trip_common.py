#!/bin/env python3
# -*- coding: utf-8 -*-

"""
@Time: 2021/1/16 15:52
@Author: yu.jiang <safemonitor@outlook.com>
@License: Apache License
@File: jenkins_trip_common.py

"""

import logging
import django
from api.tasks import check_status
from decouple import config
import time
import jenkins
from django_redis import get_redis_connection
from api.models import DeployTask, DeployLogs, BuildHistory
from api.utils.check_jenkins import JenkinsStauts
from jenkinsapi.jenkins import Jenkins
conn_redis = get_redis_connection('default')
logger = logging.getLogger('default')
server = jenkins.Jenkins(config('JENKINS_URL'), username=config('JENKINS_USER'), password=config('JENKINS_PASS'))
JENKINS_OBJ = Jenkins(config('JENKINS_URL'), username=config('JENKINS_USER'), password=config('JENKINS_PASS'))
build_history = BuildHistory()


class TripCommon(object):

    @classmethod
    def jenkins_task_status(self, common_package: str, project_name: str, build_id: int, task_id: str, user_name: str, deploy_type: str) -> dict:
        """
        任务构建状态
        :param common_package: 基础包名称
        :param project_name: 任务名称
        :param build_id: 构建编号
        :param task_id: 任务编号
        :param user_name: 用户名
        :param deploy_type: 部署类型
        :return:
        """

        job_url = server.get_job_info(common_package)['url']
        next_id = build_id
        time.sleep(10)
        while True:
            if server.get_build_info(common_package, next_id)['building']:
                time.sleep(10)
            else:
                break

        result = {}
        result['url'] = "{0}{1}".format(job_url, next_id)
        result['result'] = server.get_build_info(common_package, next_id)['result']
        queryset = DeployTask.objects.filter(task_id=task_id).first()
        if result.get("result") == 'SUCCESS':
            logger.info("任务：%strip-common基础包构建成功, 任务编号：%d" % (common_package, next_id))
            deploy_params = {
                'Deploy': 'deploy',
                'SLB': True,
                'Full_update': True,
                'on_slb': True,
            }
            logger.info('%s开始部署应用: %s,  任务ID: %s, 发布类型: %s' % (user_name, project_name, task_id, deploy_type))
            build_id = JenkinsStauts.jenkins_task_id(project_name)
            JENKINS_OBJ.build_job(project_name, params=deploy_params)
            query_deploy_task = DeployTask.objects.filter(task_id=task_id).first()
            # 写入操作日志表
            DeployLogs.objects.create(
                task_id=task_id,
                project_id=query_deploy_task.project_id,
                status=6,
                message='%s已开始部署应用 ' % (user_name,))

            # 插入构建记录到历史表
            build_history.build_id = build_id
            build_history.task_id = task_id
            build_history.app_name = project_name
            build_history.save()
            async_result = check_status.delay(project_name, build_id, task_id)
            logger.info(
                '项目%s 构建状态异步任务返回ID: %s, 状态: %s' % (project_name, str(async_result.id), str(async_result.state)))
            logger.info('代码全量部署中, 稍后请注意钉钉通知: %s' % str(deploy_params))

        else:
            # TODO 部署失败钉钉通知
            #conn_redis.delete(project_name + "_lock")
            DeployLogs.objects.create(
                task_id=task_id,
                status=5,
                message='基础包构建失败， 请联系运维查看原因！ ')

            logger.info("任务: 基础包构建失败,任务编号：%d" % (next_id))
            queryset.status = 5
            queryset.save()

        return result

    @classmethod
    def jenkins_task_id(self, job_name: str) -> int:
        """
        返回构建任务id -> number
        :param job_name:
        :return:
        """
        time.sleep(1)
        next_id = int(server.get_job_info(job_name)['nextBuildNumber'])

        return next_id
