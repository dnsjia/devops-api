#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
# @File  : ansible_cmd.py
# @Author: 往事随风
# @Email: gujiwork@outlook.com
# @Date  : 2021/5/16
# @Desc  :
"""

import logging
import time
import traceback

from celery.result import AsyncResult

from apps.cmdb.models import AnsibleExecHistory, AnsibleSyncFile
from devops_api.celery import app
from controller.ansible.inventory import BaseInventory
from controller.ansible.runner import AdHocRunner, PlayBookRunner, Options

logger = logging.getLogger('default')


@app.task
def command_shell(host_data, options, tasks, job_id):

    print('ansible异步任务开始啦！--------------------------------------------->')

    try:
        inventory = BaseInventory(host_data)
        runner = AdHocRunner(inventory, options)
        p = runner.run(tasks, "all", execution_id=str(job_id))
        print(p.results_raw)
    except BaseException as e:
        print(traceback.format_exc())
        print("异步任务执行出错: %s" % str(e))
    print('ansible异步任务返回啦！--------------------------------------------->')


@app.task
def playbook_command(host_data, options, job_id):

    print('ansible playbook异步任务开始啦！--------------------{%s}------------------------->' % job_id)

    try:
        job_id = str(job_id)
        logger.info("任务id: %s" % job_id)
        Options.playbook_path = options['playbook_path']
        Options.timeout = options['timeout']
        Options.passwords = ''
        inventory = BaseInventory(host_data)
        runner = PlayBookRunner(inventory=inventory, options=Options)
        p = runner.run(job_id=job_id)
        # runner = AdHocRunner(inventory, options)
        # p = runner.run(tasks, "all", execution_id=str(job_id))
        print(p)

    except BaseException as e:
        print(traceback.format_exc())
        print("异步任务执行出错: %s" % str(e))
    print('ansible playbook异步任务返回啦！--------------------------------------------->')


@app.task
def check_celery_status(task_id):
    while True:
        result = AsyncResult(str(task_id)).state
        h_obj = AnsibleExecHistory.objects.filter(job_id=task_id).first()
        if result == 'SUCCESS':
            h_obj.job_status = 'SUCCESS'
            h_obj.save()
            break
        elif result == 'FAILURE':
            h_obj.job_status = 'FAILURE'
            h_obj.save()
            break
        elif result == 'REVOKED':
            h_obj.job_status = 'FAILURE'
            h_obj.save()
            break
        elif result == 'STARTED':
            h_obj.job_status = 'STARTED'
            h_obj.save()
        elif result == 'RETRY':
            h_obj.job_status = 'RETRY'
            h_obj.save()
        else:
            print(result)
        time.sleep(3)


@app.task
def ansible_sendfile_celery_status(task_id):
    while True:
        result = AsyncResult(str(task_id)).state
        h_obj = AnsibleSyncFile.objects.filter(job_id=task_id).first()
        if result == 'SUCCESS':
            h_obj.job_status = 'SUCCESS'
            h_obj.save()
            break
        elif result == 'FAILURE':
            h_obj.job_status = 'FAILURE'
            h_obj.save()
            break
        elif result == 'REVOKED':
            h_obj.job_status = 'FAILURE'
            h_obj.save()
            break
        elif result == 'STARTED':
            h_obj.job_status = 'STARTED'
            h_obj.save()
        elif result == 'RETRY':
            h_obj.job_status = 'RETRY'
            h_obj.save()
        else:
            print(result)
        time.sleep(3)
