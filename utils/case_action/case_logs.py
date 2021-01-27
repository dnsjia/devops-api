# -*- coding: utf-8 -*-
# @File  : case_logs.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2021/1/22
# @Desc  :
import traceback
from django.db import transaction
from auto_case.models import TestCaseDetail
import logging

logger = logging.getLogger('default')


class CaseInsertLogs(object):

    @classmethod
    def test_case_logs(self, task_id, msg, status):
        """
        :param task_id: 测试用例任务id
        :param msg: 日志信息
        :param status: 用例执行状态
        """

        with transaction.atomic():
            task_detail_data = {
                'task_id': task_id,
                'logs': msg,
                'status': status
            }
            save_id = transaction.savepoint()
            try:
                TestCaseDetail.objects.create(**task_detail_data)
            except Exception as e:
                transaction.savepoint_rollback(save_id)
                logger.error('记录日志异常，错误原因：%s' % str(traceback.format_exc()), e)
