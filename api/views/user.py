#!/bin/env python3
# -*- coding: utf-8 -*-

"""
@Time: 2020/9/27 11:28
@Author: yu.jiang <safemonitor@outlook.com>
@License: Apache License
@File: user.py

"""
import json
from collections import defaultdict
from atlassian import Jira
import time
import requests
from decouple import config
from requests.auth import HTTPBasicAuth
from django.contrib.auth import authenticate, login
from django.db.models import Q
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
import traceback
from api.models import UserInfo, AccountType, InnerAccount
from api.utils.permissions import MyPermission
from rbac.models import Role
from api.utils.jwt_token import create_token
from utils.code import RandCode
from utils.csrf_disable import CsrfExemptSessionAuthentication
from api.utils.authorization import MyAuthentication
from utils.rest_page import StandardResultsSetPagination
from utils.selenium_config import SeleniumInit
from utils.serializer import UserInfoSerializer, AccountModelSerializers, AccountRecordrListModelSerializers
from django_redis import get_redis_connection
from utils.account_enum import AccountEnum
from api.tasks import send_dingtalk_group, deploy_send_dingtalk_work_notice, send_deploy_email
import logging
logger = logging.getLogger('default')
local_time = time.strftime('%Y-%m-%d %H:%M:%S')


class UserLoginView(APIView):
    authentication_classes =[]
    permission_classes = []

    def post(self, request, *args, **kwargs):
        """
        {'params': {'username': 'gujiwork@pigs.com', 'password': '123456', 'remember': True}}
        用户登录校验
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            #print(request.body)
            data = json.loads(request.body)['params']
            user_name = data['username']
            user_pwd = data['password']

            user = authenticate(username=user_name, password=user_pwd)

            if user and user.is_active:
                login(request, user)
                user_obj = UserInfo.objects.filter(email=user_name).first()
                permissions_list = Role.objects.filter(userinfo__user_id=user_obj.user_id).all().values('permissions__method', 'permissions__path')
                permissions = defaultdict(list)
                for i in permissions_list:
                    permissions[i.get('permissions__path')].append(i.get('permissions__method'))
                for key in permissions.keys():
                    permissions[key] = list(set(permissions[key]))
                pk = user_obj.user_id
                from django.utils import timezone
                token = create_token({'username': user_obj.username, 'permissions': permissions}, 1440)

                return JsonResponse(data={
                    "errcode": 0,
                    "msg": "登陆成功",
                    "token": token,
                    "name": user.name,
                    "avatar": user.avatar,
                    "id": pk,
                })

            return JsonResponse(data={
                "errcode": 20001,
                "msg": "邮箱或密码错误",
                "data": "null"
            }, status=status.HTTP_200_OK)

        except BaseException as e:
            logger.error("用户登录失败, 失败原因: %s" % str(traceback.format_exc()), e)
            return JsonResponse(data={
                "errcode": 99999,
                "msg": "登陆失败, 系统遇到未知错误!",
                "data": "null"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserInfoView(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        """
        获取单个用户信息
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            search_user = request.GET.get('search', None)
            if search_user:
                query_user = UserInfo.objects.filter(Q(username__contains=search_user)|Q(email__contains=search_user))
                ser = UserInfoSerializer(query_user, many=True)
                return JsonResponse(data={'UserInfo': ser.data}, safe=False)

            return JsonResponse(data={
                "errcode": 1009,
                "msg": "无法获取用户信息",
                "data": "null"
            }, json_dumps_params={'ensure_ascii': False})

        except BaseException as e:
            logger.error("获取用户信息失败: %s" % str(traceback.format_exc()), e)
            return JsonResponse(data={
                "errcode": 1010,
                "msg": "获取用户信息失败, 系统遇到未知错误!",
                "data": "null"
            }, json_dumps_params={'ensure_ascii': False})

    def delete(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return JsonResponse(data={'errcode': 403, 'msg': '无权限添加', 'data': 'null'})
        try:
            user_id = request.query_params['user_id']
            UserInfo.objects.filter(user_id=user_id).delete()
            return JsonResponse(data={'errcode': 0, 'msg': '删除用户成功'})
        except BaseException as e:
            logger.error('删除用户异常：%s' % str(traceback.format_exc()), e)
            return JsonResponse(data={'errcode': 500, 'msg': '删除用户异常！'})

    def put(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return JsonResponse(data={'errcode': 403, 'msg': '无权限添加', 'data': 'null'})
        try:
            user_id = request.data['params']
            print(user_id)
            UserInfo.objects.filter(user_id=user_id['user_id']).update(is_active=user_id['is_active'])
            return JsonResponse(data={'errcode': 0, 'msg': '更新用户成功'})
        except BaseException as e:
            logger.error('更新用户异常：%s' % str(traceback.format_exc()), e)
            return JsonResponse(data={'errcode': 500, 'msg': '更新用户异常！'})


class UserRoleView(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def put(self, request, *args, **kwargs):
        try:
            user_id = request.data['params']
            user_obj = UserInfo.objects.filter(user_id=user_id['user_id']).first()
            role_id = user_id['roles']
            user_obj.roles.clear()
            user_obj.roles.add(*role_id)
            user_obj.save()
            return JsonResponse(data={'errcode': 0, 'msg': '用户角色更新成功'})
        except BaseException as e :
            logger.error('用户角色更新异常：%s' % str(traceback.format_exc()), e)
            return JsonResponse(data={'errcode': 500, 'msg': '用户角色更新异常！'})


class AccountInfoView(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        """
        获取用户信息
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            if request.user.is_superuser:
                query_user = UserInfo.objects.all()
                paginator = StandardResultsSetPagination()
                query_users = paginator.paginate_queryset(query_user, self.request, view=self)
                serializer_user_info = UserInfoSerializer(query_users, many=True)
                page_ser = paginator.get_paginated_response(serializer_user_info.data)
                return Response(page_ser.data)

            else:
                query_user = UserInfo.objects.filter(name=request.user.name)
                paginator = StandardResultsSetPagination()
                query_users = paginator.paginate_queryset(query_user, self.request, view=self)
                serializer_user_info = UserInfoSerializer(query_users, many=True)
                page_ser = paginator.get_paginated_response(serializer_user_info.data)
                return Response(page_ser.data)

        except BaseException as e:
            logger.error("获取用户信息失败: %s" % str(traceback.format_exc()), e)
            return JsonResponse(data={
                "errcode": 1010,
                "msg": "获取用户信息失败, 系统遇到未知错误!",
                "data": "null"
            }, json_dumps_params={'ensure_ascii': False})


class CheckEmailExistView(APIView):
    permission_classes = []
    authentication_classes = [CsrfExemptSessionAuthentication, ]

    def post(self, request, *args, **kwargs):
        """
        检查用户Email是否存在
        :param request:
        :param args:
        :param kwargs:
        :return:
        """

        try:
            email = json.loads(request.body)['params']['email']
            if UserInfo.objects.filter(email=email).exists():
                return JsonResponse(data={
                    "errcode": 0,
                    "msg": "账号已存在！",
                    "data": {
                        "is_email_exits": "true"
                    }
                }, json_dumps_params={'ensure_ascii': False})

            else:
                return JsonResponse(data={
                    "errcode": 1007,
                    "msg": "账号不存在！",
                    "data": {
                        "is_email_exits": "false"
                    }
                }, json_dumps_params={'ensure_ascii': False})

        except BaseException as e:
            logger.error("检查用户email是否存在, 接口出现异常: %s" % str(traceback.format_exc()))
            # raise ServiceUnavailable
            return JsonResponse(data={
                "errcode": "1006",
                "msg": "系统异常, 请刷新重试!",
                "data": "%s" % e
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR, json_dumps_params={'ensure_ascii': False})


class SendCodeView(APIView):
    permission_classes = []
    authentication_classes = [CsrfExemptSessionAuthentication, ]

    def post(self, request, *args, **kwargs):
        """
        找回密码，发送验证码
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            email = json.loads(request.body)['params']['email']
            if not UserInfo.objects.filter(email=email).exists():
                return JsonResponse(data={'errcode': 1007, 'msg': '账号不存在'})
            code = RandCode.get_code()

            from api.tasks import send_deploy_email
            title = '找回密码'
            msg = "账号：{email}, 您当前正在进行找回密码, 您的验证码是：{code}, 打死也不要将验证码告诉别人!".format(email=email, code=code['code'])
            msg_en = f"Account number: {email}, you are trying to retrieve your password, your verification code is: {code['code']}, don't tell others about your verification code!"
            url = 'https://devops.cmdb.srv.pigs.com/'

            name = UserInfo.objects.filter(email=email).values('name')[0]['name']

            # 使用默认配置连接到redis
            cnn = get_redis_connection('default')
            cnn.set(email, code['code'])
            cnn.expire(email, 60 * 15)
            send_deploy_email.delay(email, code['code'], title, msg, msg_en, url,subject=title)
            return Response(data={'errcode': 0, 'msg': '验证码已发送,请稍后查看邮箱'})

        except BaseException as e:
            logger.error("获取验证码出错, 原因: %s" % str(traceback.format_exc()), e)
            print(traceback.format_exc())
            return Response(data={'errcode': 1008, 'msg': '获取验证码异常'})


class CheckCodeView(APIView):
    permission_classes = []
    authentication_classes = [CsrfExemptSessionAuthentication, ]

    def post(self, request, *args, **kwargs):
        """
        找回密码，校验验证码
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            code = json.loads(request.body)['params']['code']
            email = json.loads(request.body)['params']['email']

            # 使用默认配置连接到redis
            cnn = get_redis_connection('default')
            check_code = cnn.get(email)
            check_code = check_code.decode('utf-8')

            print(code, check_code)
            if int(code) != int(check_code):
                return Response(data={'errcode': 1010, 'msg': '验证码已过期或不正确'})
            return Response(data={'errcode': 0, 'msg': '验证码校验通过'})

        except BaseException as e:
            logger.error("校验验证码出现异常, 原因: %s" % str(traceback.format_exc()), e)
            print(traceback.format_exc())
            return Response(data={'errcode': 1010, 'msg': '验证码已过期或不正确'})


class ResetPwdView(APIView):
    permission_classes = []
    authentication_classes = [CsrfExemptSessionAuthentication, ]

    def post(self, request, *args, **kwargs):
        """
        找回密码， 修改新密码
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            data = json.loads(request.body)['params']
            cnn = get_redis_connection('default')
            check_code = cnn.get(data['username'])
            if check_code is not None:
                check_code = check_code.decode('utf-8')
                if int(data['code']) != int(check_code):
                    return Response(data={'errcode': 1011, 'msg': '验证码已过期或不正确'})

                user = UserInfo.objects.get(email=data['username'])
                user.set_password(data['password'])
                user.save()
                logger.info("密码修改成功, data={%s}" % str(data))
                return Response(data={'errcode': 0, 'msg': '密码修改成功'})

            return Response(data={'errcode': 1011, 'msg': '验证码已过期或不正确'})

        except BaseException as e:
            logger.error('修改密码失败, 失败原因:%s' % str(traceback.format_exc()), e)
            return Response(data={'errcode': 1012, 'msg': '密码修改失败,请重试！'})


class ChangePwdView(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def post(self, request, *args, **kwargs):
        """
        修改密码
        :param request:
        :param args:
        :param kwargs:
        :return:
        """

        try:
            data = json.loads(request.body)['params']
            email = data.get('email')
            password = data.get('password')

            if email is not None and password is not None:
                user = UserInfo.objects.get(email=email)
                user.set_password(password)
                user.save()
                logger.info("用户%s, 密码修改成功！" % str(request.user.name))
                return Response(data={'errcode': 0, 'msg': '密码修改成功'})
            return Response(data={'errcode': 1012, 'msg': '登录过期,请重新登录后再试！'})

        except BaseException as e:
            logger.error('密码修改失败: %s' % str(traceback.format_exc()), e)
            print(traceback.format_exc())
            return Response(data={'errcode': 1012, 'msg': '密码修改失败！'})


class UserAccountView(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        """
        用户账号
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        obj_data = AccountType.objects.all()
        paginator = StandardResultsSetPagination()
        page_account_list = paginator.paginate_queryset(obj_data, self.request, view=self)
        serializer_account_info = AccountModelSerializers(page_account_list, many=True)
        page_account = paginator.get_paginated_response(serializer_account_info.data)
        return Response(page_account.data)

    def post(self, request, *args, **kwargs):
        """
        审批账号申请
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        account_obj = InnerAccount()
        account_list = json.loads(request.body.decode('utf-8'))['params']
        email = request.user.email
        account_type = account_list.get('accountType')
        account_type_obj = AccountType.objects.filter(id=account_type).first()
        account_desc = account_list.get('accountDesc')
        name = request.user.name

        # 根据邮箱查询账号申请状态为2审核中,或者0同意, 如果找到了说明账号已经申请过了或者处于申请中状态, 此时则提示用户
        account_rst = InnerAccount.objects.filter(Q(account_name=email), Q(status=2), Q(account_type=int(account_type))).count()
        if account_rst > 0:
            data = {
                "errcode": 1000,
                "msg": "该{}正在审批中！".format(account_type_obj.account_type),
                "email": email
            }
            return JsonResponse(data=data)

        account_agree_status = InnerAccount.objects.filter(Q(account_name=email), Q(status=0), Q(account_type=int(account_type))).count()
        if account_agree_status > 0:
            data = {
                "errcode": 402,
                "msg": "{}已存在！".format(account_type_obj.account_type),
                "email": email
            }
            return JsonResponse(data=data)
        try:
            account_obj.id = None
            account_obj.name = name
            account_obj.account_type = int(account_type)
            account_obj.account_zh_desc = account_type_obj.account_type
            account_obj.reasons = str(account_desc).strip()
            account_obj.status = 2
            account_obj.account_name = email
            account_obj.save()
            data = {
                "errcode": 0,
                "msg": "提交成功,请耐心等待管理审核",
                "email": email
            }
            # todo 判断任务状态
            logger.info('%s帐号提交成功, 请耐心等待管理审核' % email)
            # logger.info('发送dingtalk通知')

            ding_data = {
                'msg': '',
                'title': '帐号申请通知',
                'commit': '',
                'name': name
            }
            result = send_dingtalk_group.delay(ding_data)
            logger.info('异步任务返回ID: %s, 状态: %s' % (str(result.id), str(result.state)))
            return JsonResponse(data=data)

        except BaseException as e:
            logger.error('审核用户账号时出现异常: %s' % str(traceback.format_exc()), e)
            data = {
                "errcode": 400,
                "msg": "提交异常,请联系管理员处理！",
                "email": email
            }
            return JsonResponse(data=data)


class UserAccountRecordView(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        """
        列出账号
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            if request.user.is_superuser:
                obj_account_list = InnerAccount.objects.all()
                paginator = StandardResultsSetPagination()
                page_account_list = paginator.paginate_queryset(obj_account_list, self.request, view=self)
                serializer_account_info = AccountRecordrListModelSerializers(page_account_list, many=True)
                page_account_record = paginator.get_paginated_response(serializer_account_info.data)
                return Response(page_account_record.data)
            else:
                obj_account_list = InnerAccount.objects.filter(name=request.user.name)
                paginator = StandardResultsSetPagination()
                page_account_list = paginator.paginate_queryset(obj_account_list, self.request, view=self)
                serializer_account_info = AccountRecordrListModelSerializers(page_account_list, many=True)
                page_account_record = paginator.get_paginated_response(serializer_account_info.data)
                return Response(page_account_record.data)

        except BaseException as e :
            logger.error('系统出现异常: %s' % str(traceback.format_exc()), e)
            return JsonResponse(data={
                "errcode": "1006",
                "msg": "系统异常, 请刷新重试!",
                "data": "null"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR, json_dumps_params={'ensure_ascii': False})

    def put(self, request, *args, **kwargs):
        """
        账号申请状态，拒绝
        :param request:
        :return:
        """
        data = json.loads(request.body.decode('utf-8'))['params']
        if request.user.is_superuser:
            queryset = InnerAccount.objects.filter(id=data.get('id')).first()
            if queryset.status == 2:
                name = queryset.name
                email = queryset.account_name
                queryset.status = 1
                queryset.save()
                user_id = UserInfo.objects.filter(email=email).first()
                try:
                    data = {
                        'title': '账号申请已被拒绝',
                        'msg': f'【账号类型】 \n  \n {queryset.account_zh_desc}  \n  您发起的帐号申请已被拒绝, 详细原因请咨询管理员! \n {local_time}',
                        'user_id': user_id.user_id
                    }

                    logger.info('已拒绝该用户的申请, 开始发送异步通知')
                    result = deploy_send_dingtalk_work_notice.delay(data)
                    logger.info('异步任务返回ID: %s, 状态: %s' % (str(result.id), str(result.state)))

                except BaseException as e:
                    logger.error(e)

                return JsonResponse(data={
                    "msg": "已拒绝该用户的申请！",
                    "errcode": 0,
                })
        else:
            return JsonResponse(data={'errcode': 403, 'msg': '你无权操作！'})

    def post(self, request, *args, **kwargs):
        """
        账号申请状态修改, 同意则创建对应的账号
        1.内网SVN账号 2.内网GIT账号 3.内网JIRA账号
        4.内网网盘账号 5.内网日志平台 6.生产日志平台
        :param request:
        :return:
        """
        data = json.loads(request.body.decode('utf-8'))['params']
        if request.user.is_superuser:
            queryset = InnerAccount.objects.filter(id=data.get('id')).first()
            email = queryset.account_name
            username = UserInfo.objects.filter(email=email).values('username').first()
            password = RandCode.random_password()
            name = UserInfo.objects.filter(email=email).values('name').first()
            mobile = UserInfo.objects.filter(email=email).values('mobile').first()
            title = '帐号开通提醒'
            msg = '您申请的帐号已经开通， 用户名：%s, 请妥善保管（%s）密码！' % (str(email), str(password))
            msg_en = 'Your account has been opened. User name: %s Please keep your password! (%s)' % (
                str(email),
                str(password)
            )

            if queryset.status == 2:  # 待审核的状态
                logger.info("当前申请的账号类型：%d" % int(queryset.account_type))
                if queryset.account_type == AccountEnum.INNER_SVN_ACCOUNT.value:
                    bro = SeleniumInit.create_windows(url=config('SVN_URL') + '/svnadmin/login.php')
                    time.sleep(2)
                    bro.find_element_by_id('loginname').send_keys(config('SVN_USER'))
                    bro.find_element_by_id('loginpass').send_keys(config('SVN_PASS'))
                    bro.find_element_by_class_name('addbtn').click()
                    time.sleep(0.5)
                    bro.get(url=config('SVN_URL') + '/svnadmin/usercreate.php')
                    logger.info("开始创建svn用户：%s, 密码：%s" % (email, password))
                    bro.find_element_by_id('username').send_keys(email)
                    bro.find_element_by_id('password').send_keys(password)
                    bro.find_element_by_id('password2').send_keys(password)
                    bro.find_element_by_xpath('//*[@id="textarea"]/div/form/div[4]/input').click()
                    result_msg = bro.find_element_by_xpath('//*[@id="textarea"]/div[1]/div[2]/ul').text
                    logger.info("开始加入Users用户组,加入的用户是：%s" % email)
                    bro.get(url=config('SVN_URL') + '/svnadmin/usergroupassign.php')
                    bro.find_element_by_xpath('//*[@id="textarea"]/form/table/tbody/tr/td[1]/div/input').send_keys(email)
                    bro.find_element_by_xpath('//*[@id="selectallusers"]').click()
                    bro.find_element_by_xpath('//*[@id="textarea"]/form/table/tbody/tr/td[3]/div/input').send_keys('user')
                    bro.find_element_by_xpath('//*[@id="selectallgroups"]').click()
                    bro.find_element_by_class_name('anbtn').click()
                    result_group_msg = bro.find_element_by_xpath('//*[@id="textarea"]/div/div[2]/ul/li').text

                    if 'successfully' in result_msg and 'is now a member of group user' in result_group_msg:
                        queryset.status = 0
                        queryset.save()
                        # TODO 邮件提醒, 任务状态暂未处理
                        url = 'http://svn.srv.pigs.com/svn/svn-repo'
                        logger.info(msg + '开始发送异步通知')
                        result = send_deploy_email.delay(email, name['name'], title, msg, msg_en, url, subject=title)
                        logger.info('异步任务返回ID: %s, 状态: %s' % (str(result.id), str(result.state)))
                        return JsonResponse(data={"msg": "SVN用户创建成功", "errcode": 0})

                    else:
                        logger.error('SVN用户创建失败, status:400')
                        return JsonResponse(data={"msg": "SVN用户创建失败！", "errcode": 1000})

                elif queryset.account_type == AccountEnum.INNER_GIT_ACCOUNT.value:
                    post_data = {
                        "source_id": 0,
                        "username": username['username'],  # Gogs 账号只能以用户名创建
                        "email": email,
                        "login_name": email,
                        "password": password,
                    }
                    GOGS_TOKEN = config('GOGS_TOKEN')
                    GOGS_HEADERS = {
                        "Authorization": "token {0}".format(GOGS_TOKEN)
                    }

                    git_rsp = requests.post(url=str(config('GOGS_API')) + '/api/v1/admin/users', data=post_data,
                                            headers=GOGS_HEADERS)
                    logger.info("创建Gogs用户返回状态码：%d" % git_rsp.status_code)
                    git_rsp_content = git_rsp.content.decode('utf-8')
                    logger.info("创建Gogs用户返回信息：%s" % str(git_rsp_content))
                    if git_rsp.status_code == 422:
                        logger.error('Gogs http code: 422')
                        return JsonResponse(data={
                            'errcode': 422,
                            'msg': json.loads(git_rsp_content)['message']
                        })
                    elif git_rsp.status_code == 201:
                        queryset.status = 0
                        queryset.save()
                        logger.info('Gogs用户创建成功：%s, %s' % (email, password))
                        url = 'http://git.srv.pigs.com/'
                        logger.info('发送钉钉异步通知')
                        result = send_deploy_email.delay(email, name['name'], title, msg, msg_en, url, subject=title)
                        logger.info('异步任务返回ID: %s, 状态: %s' % (str(result.id), str(result.state)))
                        return JsonResponse(data={
                            'errcode': 0,
                            'msg': "User created successfully"
                        })
                    else:
                        logger.error('Gogs创建失败, 返回状态码:%s' % str(git_rsp.status_code))
                        return JsonResponse(data={'msg': '服务异常!', "errcode": 500}, status=500)

                elif queryset.account_type == AccountEnum.INNER_JIRA_ACCOUNT.value:

                    jira = Jira(url=config('JIRA_URL'), username=config('SVN_USER'), password=config('SVN_PASS'))
                    logger.info("开始创建Jira平台账号：%s, 密码：%s" % (email, password))
                    try:
                        jira_result = jira.user_create(email, email, name['name'], password=password)
                        logger.info("创建Jira账号返回信息：%s" % str(jira_result))
                        logger.info("用户：%s, 加入的默认权限组：技术部" % email)
                        # TODO 加入Group
                        group_result = jira.add_user_to_group(email, "技术部")
                        logger.info("返回信息，%s" % str(group_result))

                        queryset.status = 0
                        queryset.save()
                        url = 'http://jira.pigs.com/'
                        logger.info('Jira用户创建成功, 发送异步通知')
                        result = send_deploy_email.delay(email, name['name'], title, msg, msg_en, url, subject=title)
                        logger.info('异步任务返回ID: %s, 状态: %s' % (str(result.id), str(result.state)))
                        return JsonResponse(data={"msg": "Jira用户创建成功！", "errcode": 0})

                    except BaseException as e:
                        logger.error("创建用户异常: %s" % str(traceback.format_exc()))
                        return JsonResponse(data={"msg": "创建Jira用户失败", "errcode": 400})

                elif queryset.account_type == AccountEnum.INNER_PAN_DISK_ACCOUNT.value:
                    bro = SeleniumInit.create_windows(url=config('PAN_URL'))
                    time.sleep(2)
                    bro.find_element_by_id('id_email').send_keys(email)
                    bro.find_element_by_id('id_password1').send_keys(password)
                    bro.find_element_by_id('id_password2').send_keys(password)
                    bro.find_element_by_class_name('submit').click()
                    time.sleep(5)

                    if '注册成功' in bro.find_element_by_xpath('//*[@id="main"]/div[1]/p').text:
                        queryset.status = 0
                        queryset.save()
                        url = 'http://pan.pigs.com/accounts/login/?next=/'
                        logger.info('网盘用户注册成功，请等待管理员激活！')
                        result = send_deploy_email.delay(email, name['name'], title, msg, msg_en, url, subject=title)
                        logger.info('异步任务返回ID: %s, 状态: %s' % (str(result.id), str(result.state)))
                        return JsonResponse(data={"msg": "网盘用户注册成功，请等待管理员激活！", "errcode": 0})

                    else:
                        logger.error('网盘用户创建失败: %s' % str(bro.find_element_by_xpath('//*[@id="main"]/div[1]/p').text))
                        return JsonResponse(data={"msg": "网盘用户创建失败！", "errcode": 1000})

                elif queryset.account_type == AccountEnum.INNER_LOGS_ACCOUNT.value:

                    headers = {
                        "Content-Type": "application/json"
                    }

                    api_url = config('INNER_ELASTIC') + '/_shield/user/{}?pretty'.format(email)

                    data = {
                        "password": password,
                        "roles": ["_test"],
                        "full_name": name['name'],
                        "email": email,
                    }
                    auth = HTTPBasicAuth(config('INNER_ELASTIC_USER'), config('INNER_ELASTIC_PASS'))
                    logger.info("开始创建内网日志平台账号：%s" % data)
                    kibana_result = requests.post(url=api_url, data=json.dumps(data), headers=headers, auth=auth)
                    logger.info("创建内网日志平台账号返回信息：%s" % str(kibana_result.text))
                    if kibana_result.status_code == 200:
                        queryset.status = 0
                        queryset.save()
                        url = 'http://logs.develop.test.pigs.com/login'
                        logger.info('内网日志平台用户创建成功,  开始发送异步通知')
                        result = send_deploy_email.delay(email, name['name'], title, msg, msg_en, url, subject=title)
                        logger.info('异步任务返回ID: %s, 状态: %s' % (str(result.id), str(result.state)))
                        return JsonResponse(data={
                            "msg": "内网日志平台用户创建成功！",
                            "errcode": 0
                        })
                    else:
                        logger.error('创建内网日志平台用户失败: %s' % str(name))
                        return JsonResponse(data={"msg": "创建内网日志平台用户失败", "errcode": 1000})

                elif queryset.account_type == AccountEnum.PROD_LOGS_ACCOUNT.value:
                    headers = {
                        "Content-Type": "application/json"
                    }

                    api_url = config('PROD_ELASTIC') + '/_shield/user/{}?pretty'.format(email)
                    logger.info(api_url)
                    data = {
                        "password": password,
                        "roles": ["dev_group"],
                        "full_name": name['name'],
                        "email": email,
                    }
                    auth = HTTPBasicAuth(config('PROD_ELASTIC_USER'), config('PROD_ELASTIC_PASS'))
                    logger.info("开始创建生产环境日志平台账号：%s" % str(data))
                    kibana_result = requests.post(url=api_url, data=json.dumps(data), headers=headers, auth=auth)
                    logger.info("创建生产环境日志平台账号返回信息：%s" % str(kibana_result.text))
                    if kibana_result.status_code == 200:
                        queryset.status = 0
                        queryset.save()
                        url = 'http://kibana.cmdb.pigs.com/login'
                        logger.info('生产环境日志平台用户创建成功, 发送异步通知')
                        result = send_deploy_email.delay(email, name['name'], title, msg, msg_en, url, subject=title)
                        logger.info('异步任务返回ID: %s, 状态: %s' % (str(result.id), str(result.state)))
                        return JsonResponse(data={
                            "msg": "生产环境日志平台用户创建成功！",
                            "errcode": 0
                        })
                    else:
                        logger.error('创建生产环境日志平台用户失败, status： 400')
                        return JsonResponse(data={"msg": "创建生产环境日志平台用户失败", "errcode": 400})

                elif queryset.account_type == AccountEnum.PROD_DB_ACCOUNT.value:
                    from utils.aliyun import AliYunInit
                    aliyun = AliYunInit()
                    _create_ram_user = aliyun.create_ram_user(
                        user_name=username['username'],
                        display_name=name['name'],
                        mobile_phone=mobile['mobile'],
                        email=email
                    )
                    if not _create_ram_user:
                        return JsonResponse(data={
                            "msg": "RAM用户创建失败！",
                            "errcode": 1000
                        })

                    _update_login_profile = aliyun.update_login_profile(user_name=username['username'], password=password)
                    if not _update_login_profile:
                        return JsonResponse(data={
                            "msg": "更新RAM用户权限失败！",
                            "errcode": 1000
                        })

                    _add_ram_user_to_group = aliyun.add_ram_user_to_group(user_name=username['username'])
                    if not _add_ram_user_to_group:
                        return JsonResponse(data={
                            "msg": "更新RAM用户权限失败！",
                            "errcode": 1000
                        })

                    # _create_rds_account = aliyun.create_rds_account(
                    #     account_name=username['username'],
                    #     account_password=password,
                    #     account_desc=name['first_name']
                    # )
                    # if not _create_rds_account:
                    #     return JsonResponse(data={
                    #         "msg": "创建RDS用户失败！",
                    #         "status": 400
                    #     })
                    #
                    # _grant_rds_account_privilege = aliyun.grant_rds_account_privilege(account_name=username['username'])
                    # if not _grant_rds_account_privilege:
                    #     return JsonResponse(data={
                    #         "msg": "更新RDS用户权限失败！",
                    #         "status": 400
                    #     })

                    queryset.status = 0
                    queryset.save()
                    url = 'https://signin.aliyun.com/login.htm'
                    logger.info("用户名：%s, 密码：%s, 邮箱：%s" % (username['username'], password, email))
                    logger.info('RAM/RDS用户创建成功！, 发送异步通知')
                    msg = '您申请的帐号已经开通， 用户名：%s, 请妥善保管（%s）密码！' % (
                        str(username['username'] + '@pigs.onaliyun.com'),
                        str(password))
                    msg_en = 'Your account has been opened. User name: %s Please keep your password! (%s)' % (
                        str(username['username'] + '@pigs.onaliyun.com'),
                        str(password)
                    )

                    result = send_deploy_email.delay(email, name['name'], title, msg, msg_en, url, subject=title)
                    logger.info('异步任务返回ID: %s, 状态: %s' % (str(result.id), str(result.state)))

                    return JsonResponse(data={
                        "msg": "RAM/RDS用户创建成功！",
                        "errcode": 0
                    })

            else:
                return JsonResponse(data={'msg': '操作不合法！只有待审核的状态才可以创建', 'errcode': 1000})
        else:
            return JsonResponse(data={'errcode': 403, 'msg': '你无权操作！'})