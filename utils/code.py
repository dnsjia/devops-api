#!/bin/env python3
# -*- coding: utf-8 -*-

"""
@Time: 2020/10/12 15:38
@Author: yu.jiang <safemonitor@outlook.com>
@License: Apache License
@File: code.py

"""

import random
import string
import uuid


class RandCode():
    @classmethod
    def get_code(self):
        """
        发送6位验证码
        :return:
        """
        code = {}
        num = '123456789'
        send_message_code = ''.join(random.choice(num) for i in range(6))
        # send_message_code = ''.join(random.choice(string.digits) for i in range(6))
        code["code"] = send_message_code

        return code

    @classmethod
    def random_password(pass_len=12, chars=string.ascii_letters + string.digits):
        """
        生成随机密码
        :param length: 长度
        :param chars: 随机字母
        :return:
        """
        password = ''.join([random.choice(chars) for i in range(18)])
        return password

    @classmethod
    def ticket_number_code(self):
        """
        生成随机工单编号
        """
        code = ""
        for i in range(8):
            add_num = str(random.randrange(0,9))
            add_al = chr(random.randrange(65,91))
            # chr转换为A-Z大写。print(chr(90))#65-90任意生成A-Z
            sj = random.choice([add_num,add_al,add_al,add_num])
            # str.lower()转换为小写，为了保证概率，将_add_num写两遍，这样，字母和数字概率一样了
            code = "".join([sj,code])
        return code

    @staticmethod
    def uuid1_hex():
        """
        return uuid1 hex string
        eg: 23f87b528d0f11e696a7f45c89a84eed
        """
        return uuid.uuid1().hex