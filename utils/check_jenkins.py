#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
@Author: 往事随风
@Mail: gujiwork@outlook.com
@File:check_jenkins.py
@Time:2020/6/4 17:47
"""

import logging
from decouple import config
import time
import jenkins
from api.models import DeployTask, SyncJobHistory
from celery_tasks import tasks

logger = logging.getLogger('default')
server = jenkins.Jenkins(config('JENKINS_URL'), username=config('JENKINS_USER'),password=config('JENKINS_PASS'))


class JenkinsStauts(object):

    @classmethod
    def jenkins_task_status(self, job_name: str, build_id: int, pk: int) -> dict:
        """
        任务构建状态
        :param job_name: 任务名称
        :param build_id: 任务编号
        :return:
        """

        job_url = server.get_job_info(job_name)['url']
        next_id = build_id
        time.sleep(10)
        while True:
            if server.get_build_info(job_name, next_id)['building'] == True:
                time.sleep(10)
            else:
                break

        result = {}
        result['url'] = "{0}{1}".format(job_url, next_id)
        result['result'] = server.get_build_info(job_name, next_id)['result']

        queryset = DeployTask.objects.filter(id=pk).first()
        if result.get("result") == 'SUCCESS':
            logger.info("任务：%s构建成功,任务编号：%d" % (job_name, next_id))

            # 任务构建成功后调用异步sync_job_code_cluster方法自动同步集群项目
            # TODO 写操作审计日志， A机器已部署完毕, 等待同步集群代码
            logger.info("2分钟后开始将：%s 代码A1同步集群A2机器" % job_name)
            rsyc_result = tasks.sync_code_job_cluster.delay(job_name, pk)
            logger.info('项目%s 集群同步构建状态异步任务返回ID: %s, 状态: %s' % (job_name, str(rsyc_result.id), str(rsyc_result.state)))
            # todo 这里要判断异步任务完成状态, 任务成功则修改部署状态
            # 修改构建状态4为部署成功
            queryset.status = 4
            queryset.save()

        else:
            # TODO 钉钉通知， 写操作审计日志， 部署失败, 请联系运维处理!
            logger.info("任务：%s构建失败,任务编号：%d" % (job_name, next_id))
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

    @classmethod
    def jenkins_sync_status(self, job_name: str, build_id: int) -> dict:
        """
        集群同步任务构建状态
        :param job_name: 任务名称
        :param build_id: 任务编号
        :return:
        """

        job_url = server.get_job_info(job_name)['url']
        time.sleep(10)
        while True:
            if server.get_build_info(job_name, build_id)['building'] == True:
                time.sleep(10)
            else:
                break

        result = {}
        result['url'] = "{0}{1}".format(job_url, build_id)
        result['result'] = server.get_build_info(job_name, build_id)['result']

        queryset_2 = SyncJobHistory.objects.filter(sync_id=build_id).first()
        if result.get("result") == 'SUCCESS':
            # TODO 集群数据同步完毕, 已完成版本上线
            logger.info("任务：%s构建成功,任务编号：%d" % (job_name, build_id))
            queryset_2.build_status = 'SUCCESS'
            queryset_2.save()
        else:
            # todo 集群数据同步失败, 请联系运维手动处理
            logger.info("任务：%s构建失败,任务编号：%d" % (job_name, build_id))
            queryset_2.build_status = 'FAIL'
            queryset_2.save()

        return result