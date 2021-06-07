#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
@Time: 2020/9/27 11:28
@Author: yu.jiang <safemonitor@outlook.com>
@License: Apache License
@File: user.py
"""

import logging
import traceback
from collections import defaultdict
from decouple import config

from django.contrib.auth import authenticate, login
from django.db.models import Q
from django.http import JsonResponse
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.views import APIView

from apps.account.models import User
from apps.account.serializers.users import UserInfoSerializer
from apps.rbac.models import Role
from utils.authorization import MyAuthentication
from utils.http_response import APIResponse
from utils.jwt_token import create_token
from utils.csrf_disable import CsrfExemptSessionAuthentication
from utils.code import RandCode
from utils.pagination import MyPageNumberPagination
from utils.permissions import MyPermission

logger = logging.getLogger('default')


class UserLoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        """
        {'username': 'gujiwork@pigs.com', 'password': '123456', 'remember': True}
        用户登录校验
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        request_id = request.META.get("HTTP_X_REQUEST_ID", "")
        try:
            data = request.data
            user_name = data['username']
            user_pwd = data['password']
            user = authenticate(username=user_name, password=user_pwd)

            if user and user.is_active:
                login(request, user)
                user_obj = User.objects.filter(email=user_name).first()
                permissions_list = Role.objects.filter(user__id=user_obj.id).all().values(
                    'permissions__method', 'permissions__path'
                )
                permissions = defaultdict(list)
                for i in permissions_list:
                    permissions[i.get('permissions__path')].append(i.get('permissions__method'))
                for key in permissions.keys():
                    permissions[key] = list(set(permissions[key]))
                pk = user_obj.id

                token = create_token({'username': user_obj.username, 'permissions': permissions}, 1440)
                data = {"token": token, "name": user.name, "avatar": user.avatar, "id": pk}
                return APIResponse(data=data)

            return APIResponse(errcode=20001, errmsg='邮箱或密码错误', status=status.HTTP_200_OK, request_id=request_id)

        except BaseException as e:
            logger.error("用户登录失败, 失败原因: %s" % str(traceback.format_exc()))
            logger.error(e)
            return APIResponse(
                errcode=99999, errmsg='登陆失败, 系统遇到未知错误!',
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                request_id=request_id
            )


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
            data = request.data
            if User.objects.filter(email=data['email']).exists():
                return APIResponse(errcode=0, errmsg='账号已存在!')

            else:
                return APIResponse(errcode=4002, errmsg='账号不存在!')

        except Exception:
            return APIResponse(errcode=5001, errmsg='系统异常，请刷新后重试！')


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
            data = request.data
            email = data['email']
            if not User.objects.filter(email=email).exists():
                return JsonResponse(data={'errcode': 1007, 'msg': '账号不存在'})
            code = RandCode.get_code()

            from tasks.email import send_email
            title = '找回密码'
            msg = "账号：{email}, 您当前正在进行找回密码, 您的验证码是：{code}, 打死也不要将验证码告诉别人!".format(email=email, code=code['code'])
            msg_en = f"Account number: {email}, you are trying to retrieve your password, your verification code is: {code['code']}, don't tell others about your verification code!"

            # 使用默认配置连接到redis
            conn = get_redis_connection('default')
            conn.set(email, code['code'])
            conn.expire(email, 60 * 15)
            send_email.delay(email, code['code'], title, msg, msg_en, config('DOMAIN_URL'), subject=title)
            return APIResponse(errcode=0, errmsg='验证码已发送,请稍后查看邮箱')

        except BaseException as e:
            logger.error("获取验证码出错, 原因: %s" % str(traceback.format_exc()))
            print(traceback.format_exc())
            return APIResponse(errcode=1008, errmsg='获取验证码异常')


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
            data = request.data
            code = data['code']
            email = data['email']

            # 使用默认配置连接到redis
            conn = get_redis_connection('default')
            check_code = conn.get(email)
            check_code = check_code.decode('utf-8')

            print(code, check_code)
            if int(code) != int(check_code):
                return APIResponse(errcode=1010, errmsg='验证码已过期或不正确')
            return APIResponse(errcode=0, errmsg='验证码校验通过')

        except BaseException as e:
            logger.error("校验验证码出现异常, 原因: %s" % str(traceback.format_exc()))
            print(traceback.format_exc())
            return APIResponse(errcode=1010, errmsg='验证码已过期或不正确')


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
            data = request.data
            conn = get_redis_connection('default')
            check_code = conn.get(data['username'])
            if check_code is not None:
                check_code = check_code.decode('utf-8')
                if int(data['code']) != int(check_code):
                    return APIResponse(errcode=1011, errmsg='验证码已过期或不正确')

                user = User.objects.get(email=data['username'])
                user.set_password(data['password'])
                user.save()
                logger.info("密码修改成功, data={%s}" % str(data))
                return APIResponse(errcode=0, errmsg='密码修改成功')

            return APIResponse(errcode=1011, errmsg='验证码已过期或不正确')

        except Exception as e:
            logger.error(str(e))
            logger.error('修改密码失败, 失败原因:%s' % str(traceback.format_exc()))
            return APIResponse(errcode=1012, errmsg='密码修改失败,请重试！')


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
            data = request.data
            email = data.get('email')
            password = data.get('password')
            # 修改密码时校验用户身份, 限制当前用户不能修改他人密码
            obj = User.objects.filter(email=request.user.email).values()
            if obj and request.user.email != email:
                return APIResponse(errcode=403, errmsg='无权限修改')

            if email is not None and password is not None:
                user = User.objects.get(email=email)
                user.set_password(password)
                user.save()
                logger.info("用户%s, 密码修改成功！" % str(request.user.name))
                return APIResponse(data={'msg': '密码修改成功'})
            return APIResponse(errcode=1012, errmsg='登录过期,请重新登录后再试！')

        except Exception as e:
            logger.error(str(e))
            logger.error('密码修改失败: %s' % str(traceback.format_exc()))
            return APIResponse(errcode=1012, errmsg='密码修改失败！')


class UserRoleView(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def put(self, request, *args, **kwargs):
        """
        更新用户角色
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            user_id = request.data
            user_obj = User.objects.filter(id=user_id['id']).first()
            role_id = user_id['roles']
            user_obj.roles.clear()
            user_obj.roles.add(*role_id)
            user_obj.save()
            return APIResponse(data={'msg': '用户角色更新成功'})
        except Exception as e:
            logger.error(str(e))
            logger.error('用户角色更新异常：%s' % str(traceback.format_exc()))
            return APIResponse(errcode=500, errmsg='用户角色更新异常！')


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
                search_user = request.GET.get('search', None)
                if search_user:
                    paginator = MyPageNumberPagination()
                    query_user = User.objects.filter(
                        Q(username__contains=search_user) | Q(email__contains=search_user) | Q(
                            mobile__contains=search_user) | Q(name__contains=search_user))
                    query_users = paginator.paginate_queryset(query_user, self.request, view=self)
                    ser = UserInfoSerializer(query_users, many=True)
                    page_ser = paginator.get_paginated_response(ser.data)
                    return APIResponse(data=page_ser.data)
                else:
                    query_user = User.objects.all()
                    paginator = MyPageNumberPagination()
                    query_users = paginator.paginate_queryset(query_user, self.request, view=self)
                    serializer_user_info = UserInfoSerializer(query_users, many=True)
                    page_ser = paginator.get_paginated_response(serializer_user_info.data)
                    return APIResponse(data=page_ser.data)

            else:
                query_user = User.objects.filter(name=request.user.name)
                paginator = MyPageNumberPagination()
                query_users = paginator.paginate_queryset(query_user, self.request, view=self)
                serializer_user_info = UserInfoSerializer(query_users, many=True)
                page_ser = paginator.get_paginated_response(serializer_user_info.data)
                return APIResponse(data=page_ser.data)

        except Exception as e:
            logger.error(str(e))
            logger.error("获取用户信息失败: %s" % str(traceback.format_exc()))
            return APIResponse(errcode=1010, errmsg='获取用户信息失败, 系统遇到未知错误!')

    def put(self, request, *args, **kwargs):
        """
        禁用用户登录
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        if not request.user.is_superuser:
            return APIResponse(errcode=403, errmsg='无权限修改用户')
        try:
            user_id = request.data
            print(user_id)
            User.objects.filter(id=user_id['id']).update(is_active=user_id['is_active'])
            return APIResponse(data={'msg': '更新用户成功'})
        except Exception as e:
            logger.error(str(e))
            logger.error('更新用户异常：%s' % str(traceback.format_exc()))
            return APIResponse(errcode=500, errmsg='更新用户异常！')

    def delete(self, request, *args, **kwargs):
        """
        删除用户
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        if not request.user.is_superuser:
            return APIResponse(errcode=403, errmsg='无权限删除！')
        try:
            user_id = request.query_params['id']
            User.objects.filter(id=user_id).delete()
            return APIResponse(data={'msg': '删除用户成功'})
        except Exception as e:
            logger.error(str(e))
            logger.error('删除用户异常：%s' % str(traceback.format_exc()))
            return APIResponse(errcode=500, errmsg='删除用户异常！')
