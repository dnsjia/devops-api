#!/bin/env python3
# -*- coding: utf-8 -*-

"""
@Time: 2020/11/3 22:00
@Author: yu.jiang <safemonitor@outlook.com>
@License: Apache License
@File: one_week_date.py

"""
import datetime


class WeekDate(object):

    @classmethod
    def get_current_week(self):
        """
        获取周一的日期,  通过ORM gte 对一周的数据进行聚合查询
        :return:
        """

        monday= datetime.date.today()
        one_day = datetime.timedelta(days=1)
        while monday.weekday() != 0:
            monday -= one_day

        return monday