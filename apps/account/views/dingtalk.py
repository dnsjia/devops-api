#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
@Time: 2020/10/2 9:16
@Author: yu.jiang <safemonitor@outlook.com>
@License: Apache License
@File: dingtalk.py
"""

import traceback
import base64
import hmac
import json
import time
import logging
from urllib import parse
from hashlib import sha256
from collections import defaultdict

from django.contrib.auth.hashers import make_password
from rest_framework.response import Response
from rest_framework_jwt.settings import api_settings
from rest_framework.views import APIView
from decouple import config

from apps.account.models import User
from utils.http_response import APIResponse
from utils.jwt_token import create_token
from utils.http_requests import RequestResult
from apps.rbac.models import Role
logger = logging.getLogger('default')


class DingLogin(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        """
        获取钉钉配置
        :param request:0
        :return:
        """
        # 扫码登录id
        request_id = request.META.get("HTTP_X_REQUEST_ID", "")
        try:
            app_id = config('DING_QR_CODE_APP_ID')
        except Exception as e:
            logger.error(e)
            return APIResponse(errcode=10001, errmsg="未配置钉钉应用id", request_id=request_id)

        return APIResponse(data={"app_id": app_id})

    def post(self, request, *args, **kwargs):
        """
        获取钉钉登录临时code
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        request_id = request.META.get("HTTP_X_REQUEST_ID", "")
        try:
            login_tmp_code = request.data
            login_tmp_code_data = RequestResult.get(login_tmp_code)

            if login_tmp_code_data.get('errcode') == '-1':
                return APIResponse(errcode=10002, errmsg="请求出错", request_id=request_id)

            if login_tmp_code_data['code'] != 200:
                logger.error('获取钉钉临时code失败: data={%s}' % login_tmp_code_data)
                return APIResponse(errcode=login_tmp_code_data['code'], errmsg=login_tmp_code_data['msg'])
            else:
                return Response(data={'errcode': 0, 'msg': login_tmp_code_data['msg']})

        except BaseException as e:
            logger.error('钉钉登陆失败, 异常原因: %s' % str(traceback.format_exc()))
            return APIResponse(errcode=500, errmsg='钉钉登陆失败:%s' % str(e))


class DingCallBack(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        """
        钉钉登录回调
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        data = request.data
        code = data['code']
        app_id = config('DING_QR_CODE_APP_ID')
        app_secret = config('DING_QR_CODE_APP_SECRET')
        ding_request_url = config('DING_REQUEST_URL')
        request_id = request.META.get("HTTP_X_REQUEST_ID", "")
        dingding_login_email_suffix = config('DING_LOGIN_EMAIL_SUFFIX')
        t = time.time()
        timestamp = str((int(round(t * 1000))))
        # 1、构造签名
        signature = base64.b64encode(hmac.new(app_secret.encode('utf-8'),
                                              timestamp.encode('utf-8'), digestmod=sha256).digest())
        sign = parse.quote(signature.decode("utf-8"))
        # 2、请求接口，换取钉钉用户名
        get_user_url = f'{ding_request_url}/sns/getuserinfo_bycode?signature={sign}&timestamp={timestamp}&accessKey={app_id}'
        data = json.dumps({'tmp_auth_code': code})
        user_data = RequestResult.post(
            get_user_url, data=data, headers={'Content-Type': 'application/json'}
        )

        if user_data.get('errcode') == '-1':
            return APIResponse(errcode=user_data['errcode'], errmsg=user_data['errmsg'], request_id=request_id)
        elif user_data['errcode'] != 0:
            logger.error('钉钉登录失败, 异常原因:%s' % str(user_data))
            return APIResponse(errcode=user_data['errcode'], errmsg=user_data['errmsg'], request_id=request_id)

        # 3、获取企业凭证
        d_app_key = config('DING_APP_KEY')
        d_app_secret = config('DING_APP_SECRET')
        get_token_url = f'{ding_request_url}/gettoken?appkey={d_app_key}&appsecret={d_app_secret}'
        token_data = RequestResult.get(get_token_url)
        if token_data.get('errcode') == '-1':
            return APIResponse(errcode=token_data['errcode'], errmsg=token_data['errmsg'], request_id=request_id)

        logger.info("根据临时code获取企业凭证, 返回信息: %s" % (str(token_data)))
        access_token = token_data['access_token']
        union_id = user_data['user_info']['unionid']
        # 4、拿到access_token的值， 根据unionid 获取userid
        get_user_union_url = f'{ding_request_url}/user/getUseridByUnionid?access_token={access_token}&unionid={union_id}'
        union_data = RequestResult.get(get_user_union_url)
        if union_data.get('errcode') == '-1':
            return APIResponse(errcode=union_data['errcode'], errmsg=union_data['errmsg'], request_id=request_id)
        # if not union_data['errcode'] == 0:
        #     return JsonResponse(data={'code': 500, 'msg': '该ip不在白名单之中'})
        logger.info("根据unionid获取userid, 返回信息： %s" % (str(union_data)))
        if union_data['errcode'] == 60020:
            logger.error('白名单授权失败, 请前往钉钉后台配置')
            return APIResponse(errcode=60020, errmsg='白名单授权失败!', request_id=request_id)
        elif union_data['errcode'] != 0:
            # 找不到该用户 该用户不属于本企业
            logger.warning('用户不属于当前企业, 钉钉返回信息: %s' % str(union_data))
            return APIResponse(errcode=404, errmsg='用户不属于当前企业!', request_id=request_id)

        # 根据用户userid 获取用户详情
        userid = union_data['userid']
        get_user_detail_url = f'{ding_request_url}/user/get?access_token={access_token}&userid={userid}'
        user_info_data = RequestResult.get(get_user_detail_url)
        logger.info("请求钉钉接口, 当前返回的详细信息是：%s" % user_info_data)
        if user_info_data.get('errcode') == '-1':
            return APIResponse(errcode=user_info_data['errcode'], errmsg=user_info_data['errmsg'], request_id=request_id)
        try:
            email = str(user_info_data.get('email')).split('@')
            if user_info_data.get('email') and email[-1] == dingding_login_email_suffix:
                user_obj = User.objects.filter(email=user_info_data['email']).first()
                # 用户存在且为激活状态, 直接返回token
                if user_obj and user_obj.is_active:
                    permissions_list = Role.objects.filter(user__user_id=user_obj.user_id).all().values(
                        'permissions__method', 'permissions__path'
                    )
                    permissions = defaultdict(list)
                    for i in permissions_list:
                        permissions[i.get('permissions__path')].append(i.get('permissions__method'))
                    for key in permissions.keys():
                        permissions[key] = list(set(permissions[key]))
                    pk = user_obj.user_id
                    from django.utils import timezone
                    # 登录成功,创建token
                    token = create_token({'username': user_obj.username, 'permissions': permissions}, 1440)
                    logger.info('%s用户登录成功， token: %s' % (str(user_obj.name), str(token)))
                    return APIResponse(data={
                        "token": token,
                        "name": user_obj.name,
                        "avatar": user_obj.avatar,
                        "pk": pk
                    })

                else:
                    # 首次登录 建立账号保存到数据库
                    try:
                        user_data = {'user_id': user_info_data['userid'], 'username': email[0],
                                     'last_name': user_info_data['name'][0], 'first_name': user_info_data['name'][1:],
                                     'email': user_info_data['email'], 'mobile': user_info_data['mobile'],
                                     'name': user_info_data['name'], 'job_number': user_info_data['jobnumber'],
                                     'avatar': user_info_data['avatar'], 'position': user_info_data['position'],
                                     'password': make_password('%s%s' % (email[0], user_info_data['mobile']))}
                        # uninx 时间戳转换
                        time_local = time.localtime(user_info_data['hiredDate'] / 1000)
                        hire_date = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
                        user_data['hire_date'] = hire_date

                        User.objects.update_or_create(**user_data, )
                        query_user = User.objects.filter(user_id=user_info_data['userid'])
                        if query_user.exists():
                            logger.info('已创建钉钉账号')
                            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
                            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
                            payload = jwt_payload_handler(query_user.first())
                            token = jwt_encode_handler(payload)
                            return APIResponse(data={
                                "token": token,
                                "name": user_data['name'],
                                "avatar": user_data['avatar'],
                            })
                    except BaseException as e:
                        logger.error(e)
                        logger.error('钉钉首次登录失败，获取信息出错。 原因:%s' % str(traceback.format_exc()))
                        return APIResponse(errcode=40004, errmsg="您的钉钉工作信息不完整, 请联系公司人事进行处理", request_id=request_id)
            else:
                return APIResponse(errcode=1009, errmsg="您未绑定@{}邮箱, 请联系公司人事进行邮箱绑定".format(dingding_login_email_suffix), request_id=request_id)

        except (TypeError, IndexError, ConnectionError) as e:
            logger.error('用户登录时系统出现异常, 异常原因: %s' % str(traceback.format_exc()))
            return APIResponse(errcode=1010, errmsg="系统出错!", request_id=request_id)
