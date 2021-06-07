#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
@Time: 2021/4/19 0019 上午 11:34
@Author: micheng. <safemonitor@outlook.com>
@File: time_utils.py
"""

import pytz
from datetime import date
from datetime import datetime
from datetime import timedelta

loc_tz = pytz.timezone('Asia/Shanghai')
utc_tz = pytz.timezone('UTC')


def str2datetime_by_format(dt_str, dt_format='%Y-%m-%d %H:%M:%S'):
    """时间字符串转datetime"""

    return loc_tz.localize(datetime.strptime(dt_str, dt_format))


def datetime2str_by_format(dt, dt_format='%Y-%m-%d %H:%M:%S'):
    """本地datetime转本地字符串"""

    if not dt:
        return ''
    return dt.astimezone(loc_tz).strftime(dt_format)


def date2str(dt, dt_format='%Y-%m-%d'):
    """日期转字符串"""

    if not dt:
        return ''
    return dt.strftime(dt_format)


def str2date(dt_str):
    """
    字符串转日期
    """
    dt = str2datetime_by_format(dt_str, '%Y-%m-%d')
    return dt.date()


def date2datetime(dt):
    return today().replace(year=dt.year, month=dt.month, day=dt.day)


def datetime2date_range(dt):
    """datetime转换成一天的开始和结束时间[start, end)"""

    start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start, end


def now():
    return datetime.utcnow().replace(tzinfo=utc_tz).astimezone(loc_tz)


def today():
    dt = now()
    dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    return dt


def tomorrow():
    return today() + timedelta(days=1)


def yesterday():
    return today() - timedelta(days=1)


def utcts2dt(ts):
    """UTC时间戳转Datetime"""

    dt = datetime.utcfromtimestamp(ts)
    dt = dt + timedelta(hours=8)
    return dt


def get_all_week_by_year(year):
    """获取一年所有周字符串列表"""

    week_list = []
    for i in range(1, datetime.date(year, 12, 31).isocalendar()[1] + 1):
        week = '{}-{}'.format(year, i)
        week_list.append(week)
    return week_list


def get_all_month_by_year(year):
    """获取一年所有月份字符串列表"""

    month_list = []
    for i in range(12):
        month = '{}-{}'.format(year, i + 1)
        month_list.append(month)
    return month_list


def get_all_month(dt_start, dt_end):
    """获取时间范围内所有月份"""

    month_list = []
    dvalue = dt_end.year - dt_start.year
    if dvalue == 0:
        for i in range(dt_start.month, dt_end.month + 1):
            month = '{}-{}'.format(dt_start.year, i)
            month_list.append(month)
    elif dvalue == 1:
        for i in range(dt_start.month, 13):
            month = '{}-{}'.format(dt_start.year, i)
            month_list.append(month)
        for i in range(1, dt_end.month + 1):
            month = '{}-{}'.format(dt_end.year, i)
            month_list.append(month)
    elif dvalue > 1:
        for i in range(dt_start.month, 13):
            month = '{}-{}'.format(dt_start.year, i)
            month_list.append(month)
        for i in range(1, dvalue):
            month_list.extend(get_all_month_by_year(dt_start.year + i))
        for i in range(1, dt_end.month + 1):
            month = '{}-{}'.format(dt_end.year, i)
            month_list.append(month)
    return month_list


def get_max_week_by_year(year):
    """获取一年最大周数"""

    # 取一年中最后一天的周数，如果所在年已经不是同一年，那么再减去对应星期数
    week = date(year, 12, 31).isocalendar()
    if week[0] == year:
        return week[1]
    else:
        return date(year, 12, 31 - week[2]).isocalendar()[1]


def get_all_week(dt_start, dt_end):
    """获取时间范围内所有周"""

    week_list = []
    dvalue = dt_end.year - dt_start.year
    if dvalue == 0:
        for i in range(dt_start.isocalendar()[1], dt_end.isocalendar()[1] + 1):
            week = '{}-{}'.format(dt_start.year, i)
            week_list.append(week)
    elif dvalue == 1:
        max_week = get_max_week_by_year(dt_start.year)
        for i in range(dt_start.isocalendar()[1], max_week + 1):
            week = '{}-{}'.format(dt_start.year, i)
            week_list.append(week)
        for i in range(1, dt_end.isocalendar()[1] + 1):
            week = '{}-{}'.format(dt_end.year, i)
            week_list.append(week)
    elif dvalue > 1:
        for i in range(dt_start.isocalendar()[1], dt_start.replace(month=12, day=31).isocalendar()[1] + 1):
            week = '{}-{}'.format(dt_start.year, i)
            week_list.append(week)
        for i in range(1, dvalue):
            week_list.extend(get_all_week_by_year(dt_start.year + i))
        for i in range(1, dt_end.isocalendar()[1] + 1):
            week = '{}-{}'.format(dt_end.year, i)
            week_list.append(week)
    return week_list


def tz_to_localtime(tztime):
    """
    2022-01-09T16:00Z 转换为本地时间
    """
    utc_date = datetime.strptime(tztime, "%Y-%m-%dT%H:%MZ")
    local_date = utc_date + timedelta(hours=8)
    local_date_str = datetime.strftime(local_date, '%Y-%m-%d %H:%M')
    print(local_date_str)

    return local_date_str