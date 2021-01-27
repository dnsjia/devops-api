#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : dir_and_time.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2021/1/10
# @Desc  :

from datetime import datetime, date


class DirAndTime:

    @staticmethod
    def get_current_date():
        """
        获取当前日期 格式: 2021-01-10
        :return:
        """
        try:
            # 获取当前日期
            current_date = date.today()
        except Exception as e:
            raise e
        else:
            return str(current_date)

    @staticmethod
    def get_current_time():
        """
        获取当前日期 格式: 2021-01-10 19:58:23
        :return:
        """
        try:
            # 获取当前日期
            current_time = datetime.now()
            current_time = current_time.strftime('%Y-%m-%d-%H-%M-%S')
        except Exception as e:
            raise e
        else:
            return current_time
