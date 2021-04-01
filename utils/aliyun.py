#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
@Author: 往事随风
@Mail: gujiwork@outlook.com
@File:aliyun.py
@Time:2020/6/9 16:57
"""
import json
import logging
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkrds.request.v20140815.CreateAccountRequest import CreateAccountRequest
from aliyunsdkrds.request.v20140815.GrantAccountPrivilegeRequest import GrantAccountPrivilegeRequest
from aliyunsdkram.request.v20150501.AddUserToGroupRequest import AddUserToGroupRequest
from aliyunsdkram.request.v20150501.CreateUserRequest import CreateUserRequest
from aliyunsdkram.request.v20150501.UpdateLoginProfileRequest import UpdateLoginProfileRequest
from decouple import config
logger = logging.getLogger('default')
'''
pip install aliyun-python-sdk-core
pip install aliyun-python-sdk-rds
pip install aliyun-python-sdk-ram
'''

class AliYunInit():
    def __init__(self):
        self.client = AcsClient(config('ACCESS_KEY_ID'), config('ACCESS_KEY_SECRET'), config('REGION_ID'))
        self.request = CreateAccountRequest()
        self.request.set_accept_format('json')
        self.db_instance_id = config('DB_INSTANCE_ID')

    def create_ram_user(self, user_name, display_name, mobile_phone, email):
        """
        创建RAM子帐号
        :param user_name: 用户名
        :param display_name: 中文全名
        :param mobile_phone: 手机号码
        :param email:  邮箱地址
        :return:
        """
        try:
            ram_request = CreateUserRequest()
            ram_request.set_accept_format('json')
            ram_request.set_UserName(user_name)
            ram_request.set_DisplayName(display_name)
            ram_request.set_MobilePhone("86-%s" % mobile_phone)
            ram_request.set_Email(email)

            response = self.client.do_action_with_exception(ram_request)

            rsp = json.loads(response, encoding='utf-8')
            logger.info("创建{%s}RAM子帐号返回信息：%s" %(user_name,rsp))
            return True
        except ServerException as e:
            logger.info("创建{%s}RAM子帐号失败，返回信息：%s" %(user_name,e))
            return False

    def update_login_profile(self, user_name, password, mfa=True):
        """
        更新RAM用户
        :param user_name: 用户名
        :param password: 密码
        :param mfa: 虚拟设备
        :return:
        """
        try:
            request = UpdateLoginProfileRequest()
            request.set_accept_format('json')

            request.set_UserName(user_name)
            request.set_Password(password)
            request.set_PasswordResetRequired(False)
            request.set_MFABindRequired(mfa)

            response = self.client.do_action_with_exception(request)

            rsp = json.loads(response, encoding='utf-8')
            logger.info("更新{%s}RAM用户返回信息：%s" %(user_name,rsp))
            return True
        except ServerException as e:
            logger.info("更新{%s}RAM用户失败，返回信息：%s" %(user_name, e))
            return False

    def add_ram_user_to_group(self, user_name, group_name='test'):
        """
        将RAM用户添加到特定的组
        :param user_name:
        :return:
        """
        try:
            ram_add_request = AddUserToGroupRequest()
            ram_add_request.set_accept_format('json')
            ram_add_request.set_UserName(user_name)
            ram_add_request.set_GroupName(group_name)

            response = self.client.do_action_with_exception(ram_add_request)

            rsp = json.loads(response, encoding='utf-8')
            logger.info("将{%s}RAM用户添加到特定的组: %s" %(user_name,rsp))
            return True
        except ServerException as e:
            logger.info("将{%s}RAM用户添加到特定的组失败，返回信息：%s" %(user_name, e))
            return False

    def create_rds_account(self, account_name, account_password, account_desc):
        """
        创建RDS帐号
        :param account_name:
        :param account_password:
        :param account_desc:
        :return:
        """
        try:
            self.request.set_DBInstanceId(self.db_instance_id)
            self.request.set_AccountName(account_name)
            self.request.set_AccountPassword(account_password)
            self.request.set_AccountDescription(account_desc)
            self.request.set_AccountType("Normal")

            response = self.client.do_action_with_exception(self.request)

            rsp = json.loads(response, encoding='utf-8')
            logger.info("创建{%s}RDS帐号返回信息: %s" %(account_name,rsp))
            return True
        except ServerException as e:
            logger.info("创建{%s}RDS帐号失败，返回信息：%s" %(account_name,e))
            return False

    def grant_rds_account_privilege(self, account_name, db_name='pigs'):
        '''
        设置RDS账号权限，取值：

        ReadWrite：读写
        ReadOnly：只读
        DDLOnly：仅执行DDL
        DMLOnly：只执行DML
        DBOwner：数据库所有者
        MySQL和MariaDB可传入ReadWrite、ReadOnly、DDLOnly或DMLOnly。
        '''
        try :
            rds_request = GrantAccountPrivilegeRequest()
            rds_request.set_accept_format('json')
            rds_request.set_DBInstanceId(self.db_instance_id)
            rds_request.set_AccountName(account_name)
            rds_request.set_DBName(db_name)
            rds_request.set_AccountPrivilege("ReadOnly")

            response = self.client.do_action_with_exception(rds_request)

            rsp = json.loads(response, encoding='utf-8')
            logger.info("设置{%s}RDS账号权限: %s" %(account_name, rsp))
            return True
        except ServerException as e:
            logger.info("设置{%s}RDS账号权限失败，返回信息：%s" %(account_name,e))
            return False