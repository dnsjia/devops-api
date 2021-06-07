#!/bin/env python3
# -*- coding: utf-8 -*-

"""
@Time: 2020/9/27 11:28
@Author: yu.jiang <safemonitor@outlook.com>
@License: Apache License
@File: user.py

"""

from django.conf.urls import url

from apps.account.views.dingtalk import DingLogin, DingCallBack
from apps.account.views.user import UserLoginView, CheckEmailExistView, SendCodeView, CheckCodeView, ResetPwdView, \
    ChangePwdView, AccountInfoView, UserRoleView

app_name = 'account'

urlpatterns = [
    url(r'^(?P<version>[v1|v2]+)/user/login$', UserLoginView.as_view(), name='login'),
    url(r'^(?P<version>[v1|v2]+)/user/dingding$', DingLogin.as_view(), name='ding_login'),
    url(r'^(?P<version>[v1|v2]+)/user/dingding/callback$', DingCallBack.as_view(), name='ding_callback'),
    url(r'^(?P<version>[v1|v2]+)/user/check_email_exist$', CheckEmailExistView.as_view(), name='check_email_exists'),
    url(r'^(?P<version>[v1|v2]+)/user/password/send_code$', SendCodeView.as_view(), name='send_code'),
    url(r'^(?P<version>[v1|v2]+)/user/password/check_code$', CheckCodeView.as_view(), name='check_code'),
    url(r'^(?P<version>[v1|v2]+)/user/password/reset_pwd$', ResetPwdView.as_view(), name='reset_pwd'),
    url(r'^(?P<version>[v1|v2]+)/user/password/change$', ChangePwdView.as_view(), name='change_pwd'),
    url(r'^(?P<version>[v1|v2]+)/users$', AccountInfoView.as_view(), name='account_info'),
    url(r'^(?P<version>[v1|v2]+)/user/role$', UserRoleView.as_view(), name='user_role'),

]