#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
@Author: 往事随风
@Mail: gujiwork@outlook.com
@File:check_jenkins.py
@Time:2020/6/4 17:47
"""

import logging
import random
import traceback
from decouple import config
import time
import jenkins
from django_redis import get_redis_connection
from api.models import DeployTask, SyncJobHistory, DeployLogs, Project, UserInfo
from api import tasks

conn_redis = get_redis_connection('default')
logger = logging.getLogger('default')
server = jenkins.Jenkins(config('JENKINS_URL'), username=config('JENKINS_USER'), password=config('JENKINS_PASS'))


class JenkinsStatus(object):

    @classmethod
    def jenkins_task_status(self, project_name: str, build_id: int, task_id: str) -> dict:
        """
        任务构建状态
        :param project_name: 任务名称
        :param build_id: 构建编号
        :param task_id: 任务编号
        :return:
        """

        job_url = server.get_job_info(project_name)['url']
        next_id = build_id
        time.sleep(10)
        while True:
            if server.get_build_info(project_name, next_id)['building']:
                time.sleep(10)
            else:
                break

        result = {'url': "{0}{1}".format(job_url, next_id),
                  'result': server.get_build_info(project_name, next_id)['result']}

        queryset = DeployTask.objects.filter(task_id=task_id).first()
        if result.get("result") == 'SUCCESS':
            logger.info("任务：%s构建成功, 任务编号：%d" % (project_name, next_id))

            if str(queryset.deploy_type) != 'CONTAINER':
                # TODO 写操作审计日志， A机器已部署完毕, 等待同步集群代码
                sync_job_name = config('SYNC_JOB_NAME').split(',')
                if project_name in sync_job_name:
                    logger.info("2分钟后开始将：%s代码从A1机器同步集群A2机器" % project_name)
                    DeployLogs.objects.create(task_id=task_id, status=3, message='A组机器已部署完成， 等待同步集群节点 ')
                    time.sleep(random.randint(5, 15))
                    DeployLogs.objects.create(task_id=task_id, status=3, message='正在同步集群数据， 此过程大约耗时5~15分钟! ')
                    # 任务构建成功后调用异步sync_job_code_cluster方法自动同步集群项目
                    rsyc_result = tasks.sync_code_job_cluster.delay(project_name, task_id)
                    logger.info('项目: %s 集群同步构建状态异步任务返回ID: %s, 状态: %s' % (
                        project_name, str(rsyc_result.id), str(rsyc_result.state)))
                else:
                    DeployLogs.objects.create(task_id=task_id, status=4, message='项目部署成功 ')
                    queryset = DeployTask.objects.filter(task_id=task_id).first()
                    queryset.status = 4
                    queryset.save()
                    # 释放任务锁
                    conn_redis.delete(project_name + "_lock")
                    # 通知研发人
                    try:
                        notice_user = eval(queryset.develop_user)
                        at_develop_user_list = []
                        for user in notice_user:
                            _user = user.split('@')[1]
                            at_develop_user_list.append(
                                UserInfo.objects.filter(username=_user).values('mobile')[0]['mobile'])
                        # 调用异步通知
                        data = "您负责的应用【%s】已部署上线， 部署版本： %s \n 提交人： %s  \n上线原因： %s， 请及时关注！ " % (
                            project_name, queryset.version, queryset.submit_people, queryset.title)
                        tasks.deploy_send_develop_dingtalk_group.delay(data, at_develop_user_list)
                    except BaseException as e:
                        print(e)
                        logger.error("发送研发人通知失败, 原因: %s" % str(traceback.format_exc()))

            else:
                logger.info('释放任务锁，%s' % (project_name,))
                conn_redis.delete(project_name + "_lock")
                DeployLogs.objects.create(
                    task_id=task_id,
                    status=4,
                    message='项目部署成功！ ')
                # 修改构建状态4为部署成功
                queryset = DeployTask.objects.filter(task_id=task_id).first()
                queryset.status = 4
                queryset.save()
                # 通知研发人
                try:
                    notice_user = eval(queryset.develop_user)
                    at_develop_user_list = []
                    for user in notice_user:
                        _user = user.split('@')[1]
                        at_develop_user_list.append(
                            UserInfo.objects.filter(username=_user).values('mobile')[0]['mobile'])
                    # 调用异步通知
                    data = "您负责的应用【%s】已部署上线， 部署版本： %s \n 提交人： %s  \n上线原因： %s， 请及时关注！ " % (
                        project_name, queryset.version, queryset.submit_people, queryset.title)
                    tasks.deploy_send_develop_dingtalk_group.delay(data, at_develop_user_list)
                except BaseException as e:
                    print(e)
                    logger.error("发送研发人通知失败, 原因: %s" % str(traceback.format_exc()))

        else:
            # TODO 部署失败钉钉通知
            conn_redis.delete(project_name + "_lock")
            DeployLogs.objects.create(
                task_id=task_id,
                status=6,
                message='部署失败， 请通过日志查看失败原因！ ')

            logger.info("任务: %s构建失败,任务编号：%d 释放锁:%s" % (project_name, next_id, project_name + "_lock"))
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
    def jenkins_sync_status(self, project_name: str, build_id: int, task_id: str) -> dict:
        """
        集群同步任务构建状态
        :param project_name: 项目名称
        :param build_id: 构建编号
        :param task_id: 任务编号
        :return:
        """

        job_url = server.get_job_info(project_name)['url']
        time.sleep(10)
        while True:
            if server.get_build_info(project_name, build_id)['building']:
                time.sleep(10)
            else:
                break

        result = {'url': "{0}{1}".format(job_url, build_id),
                  'result': server.get_build_info(project_name, build_id)['result']}

        queryset_2 = SyncJobHistory.objects.filter(sync_id=build_id).first()

        if result.get("result") == 'SUCCESS':
            logger.info("集群数据同步任务：%s构建成功, 任务编号：%d" % (project_name, build_id))
            queryset_2.build_status = 'SUCCESS'
            queryset_2.save()

            # 修改构建状态4为部署成功
            queryset = DeployTask.objects.filter(task_id=task_id).first()
            queryset.status = 4
            queryset.save()
            lock = Project.objects.filter(pk=queryset.project_id).first()
            logger.info("开始释放锁%s" % lock.title)
            conn_redis.delete(lock.title + "_lock")
            # 写入操作日志表
            DeployLogs.objects.create(task_id=task_id, status=4, message='集群已同步完成， 项目部署成功 ')
            # 通知研发人
            try:
                notice_user = eval(queryset.develop_user)
                at_develop_user_list = []
                for user in notice_user:
                    _user = user.split('@')[1]
                    at_develop_user_list.append(UserInfo.objects.filter(username=_user).values('mobile')[0]['mobile'])
                # 调用异步通知
                data = "您负责的应用【%s】已部署上线， 部署版本： %s \n 提交人： %s  \n上线原因： %s， 请及时关注！ " % (
                    lock.title, queryset.version, queryset.submit_people, queryset.title
                )
                tasks.deploy_send_develop_dingtalk_group.delay(data, at_develop_user_list)
            except BaseException as e:
                print(e)
                logger.error("发送研发人通知失败, 原因: %s" % str(traceback.format_exc()))

        else:
            # 集群数据同步失败, 请联系运维手动处理， 释放任务锁
            conn_redis.delete(project_name + "_lock")
            queryset = DeployTask.objects.filter(task_id=task_id).first()
            queryset.status = 5
            queryset.save()

            DeployLogs.objects.create(
                task_id=task_id,
                status=5,
                message='集群同步失败， 项目部署失败 ')

            logger.error("集群数据同步任务: %s构建失败, 任务编号: %s" % (project_name, build_id))
            queryset_2.build_status = 'FAIL'
            queryset_2.save()

        return result

    @classmethod
    def jenkins_rollback_status(self, project_name: str, build_id: int) -> dict:
        """
        回滚任务构建状态
        :param project_name: 任务名称
        :param build_id: 构建编号
        :return:
        """

        job_url = server.get_job_info(project_name)['url']
        next_id = build_id
        time.sleep(10)
        while True:
            if server.get_build_info(project_name, next_id)['building']:
                time.sleep(10)
            else:
                break
        result = {'url': "{0}{1}".format(job_url, next_id),
                  'result': server.get_build_info(project_name, next_id)['result']}

        if result.get("result") == 'SUCCESS':
            logger.info("回滚-> 任务：%s构建成功, 任务编号：%d" % (project_name, next_id))
            sync_job_name = config('SYNC_JOB_NAME').split(',')

            if project_name in sync_job_name:
                logger.info("2分钟后开始将：%s代码从A1机器同步集群A2机器" % project_name)
                time.sleep(random.randint(3, 10))
                # DeployLogs.objects.create(task_id=task_id, status=3, message='正在同步集群数据, 此过程大约耗时5~15分钟! ')
                # 任务构建成功后调用异步sync_job_code_cluster方法自动同步集群项目
                rsyc_result = tasks.rollback_sync_code_job_cluster.delay(project_name, build_id)
                logger.info('回滚-> 项目: %s 集群同步构建状态异步任务返回ID: %s, 状态: %s' % (
                    project_name, str(rsyc_result.id), str(rsyc_result.state)))
            else:
                # todo 发送回滚部署成功dingtalk通知
                logger.info('回滚任务：%s, 属于单机项目无集群机器, 跳过同步。' % project_name)
        else:
            # TODO 部署失败钉钉通知
            conn_redis.delete(project_name + "_lock")
            logger.info("回滚-> 任务: %s回滚失败, 任务编号：%d 释放锁:%s" % (project_name, next_id, project_name + "_lock"))

        return result