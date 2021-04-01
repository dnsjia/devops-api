#!/bin/env python3
# -*- coding: utf-8 -*-

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
from collections import defaultdict
from urllib import parse
from hashlib import sha256
import requests
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from rest_framework_jwt.settings import api_settings
from rest_framework.views import APIView
from decouple import config
from api.models import UserInfo
import logging

from api.utils.jwt_token import create_token
from rbac.models import Role

logger = logging.getLogger('default')


class DingConf(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        """
        获取钉钉配置
        :param request:0
        :return:
        """
        # 扫码登录id
        app_id = config('DINGDING_APP_ID')
        return JsonResponse(data={"appid": app_id, "errcode": 0, "msg": "success", })

    def post(self, request, *args, **kwargs):
        """
        获取钉钉登录临时code
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            login_tmp_code = json.loads(request.body.decode('utf-8'))
            resp = requests.get(url=login_tmp_code['params']).json()
            if resp['code'] == 200:
                return JsonResponse(data={'errcode': 0, 'msg': resp['msg']})
            else:
                logger.error('获取钉钉临时code失败: data={%s}' % (resp))
                return JsonResponse(data={'errcode': resp['code'], 'msg': resp['msg']})

        except BaseException as e:
            logger.error('钉钉登陆失败, 异常原因: %s' % str(traceback.format_exc()))
            return JsonResponse(data={'errcode': 500, 'msg': '钉钉登陆失败'})


class DingCallBack(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body.decode('utf-8'))
        code = data['params']['code']
        app_id = config('DINGDING_APP_ID')
        app_secret = config('DINGDING_APP_SECRET')

        t = time.time()
        timestamp = str((int(round(t * 1000))))
        # 构造签名
        signature = base64.b64encode(hmac.new(app_secret.encode('utf-8'),
                                              timestamp.encode('utf-8'), digestmod=sha256).digest())
        # 请求接口，换取钉钉用户名
        payload = {'tmp_auth_code': code}
        headers = {'Content-Type': 'application/json'}
        res = requests.post('https://oapi.dingtalk.com/sns/getuserinfo_bycode?signature=' + parse.quote(
            signature.decode("utf-8")) + "&timestamp=" + timestamp + "&accessKey=%s" % app_id,
                            data=json.dumps(payload), headers=headers).json()

        if not res['errcode'] == 0:
            logger.error('钉钉登录失败, 异常原因:%s' % str(res))
            return JsonResponse(data={'errcode': 401, 'msg': '钉钉登陆失败，请使用账号登录'})

        # 获取企业凭证
        d_app_key = config('D_APP_KEY')
        d_app_secret = config('D_APP_SECRET')
        token_data = requests.get('https://oapi.dingtalk.com/gettoken?appkey={appkey}&appsecret={appsecret}'
                                  .format(appkey=d_app_key,appsecret=d_app_secret)).json()

        logger.info("根据临时code获取企业凭证, 返回信息: %s" % (str(token_data)))
        access_token = token_data['access_token']
        # 拿到access_token的值， 根据unionid 获取userid
        userid_res = requests.get(
            'https://oapi.dingtalk.com/user/getUseridByUnionid?access_token={access_token}&unionid={unionid}'.format(
                access_token=access_token, unionid=res['user_info']['unionid'])).json()

        # if not userid_res['errcode'] == 0:
        #     return JsonResponse(data={'code': 500, 'msg': '该ip不在白名单之中'})
        logger.info("根据unionid获取userid, 返回信息： %s" % (str(userid_res)))
        if userid_res['errcode'] == 60020:
            logger.error('白名单授权失败, 请前往钉钉后台配置')
            return JsonResponse(data={'errcode': 60020, 'msg': '白名单授权失败!'})
        elif userid_res['errcode'] != 0:
            # 找不到该用户 该用户不属于本企业
            logger.warning('用户不属于当前企业, 钉钉返回信息: %s' % str(userid_res))
            return JsonResponse(data={'errcode': 404, 'msg': '用户不存在!', 'data': userid_res['errmsg']})

        # 根据用户userid 获取用户详情
        user_info = requests.get(
            'https://oapi.dingtalk.com/user/get?access_token={access_token}&userid={userid}'.format(
                access_token=access_token, userid=userid_res['userid'])).json(
        )
        logger.info("请求钉钉接口, 当前返回的详细信息是：%s" % (user_info))
        try:
            email = str(user_info.get('email')).split('@')
            if user_info.get('email'):
                if email[-1] == 'pigs.com':
                    user_obj = UserInfo.objects.filter(email=user_info['email']).first()
                    # 用户存在且为激活状态, 直接返回token
                    if user_obj and user_obj.is_active:
                        permissions_list = Role.objects.filter(userinfo__user_id=user_obj.user_id).all().values(
                            'permissions__method', 'permissions__path')
                        permissions = defaultdict(list)
                        for i in permissions_list:
                            permissions[i.get('permissions__path')].append(i.get('permissions__method'))
                        for key in permissions.keys():
                            permissions[key] = list(set(permissions[key]))
                        pk = user_obj.user_id
                        print("用户权限", permissions)
                        from django.utils import timezone
                        token = create_token({'username': user_obj.username, 'permissions': permissions}, 1440)

                        logger.info('%s用户登录成功， token: %s' % (str(user_obj.name),str(token)))
                        return JsonResponse(data={
                            "errcode": 0,
                            "msg": "登陆成功",
                            "token": token,
                            "name": user_obj.name,
                            "avatar": user_obj.avatar,
                        })

                    else:
                        # 首次登录 建立账号保存到数据库
                        try:
                            user_data = {'user_id': user_info['userid'], 'username': email[0],
                                         'last_name': user_info['name'][0], 'first_name': user_info['name'][1:],
                                         'email': user_info['email'], 'mobile': user_info['mobile'],
                                         'name': user_info['name'], 'job_number': user_info['jobnumber'],
                                         'avatar': user_info['avatar'], 'position': user_info['position'],
                                         'password': make_password('%s%s' % (email[0], user_info['mobile']))}
                            # uninx 时间戳转换
                            time_local = time.localtime(user_info['hiredDate'] / 1000)
                            hire_date = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
                            user_data['hire_date'] = hire_date

                            UserInfo.objects.update_or_create(**user_data, )
                            query_user = UserInfo.objects.filter(user_id=user_info['userid'])
                            if query_user.exists():
                                logger.info('已创建钉钉账户')
                                jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
                                jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
                                payload = jwt_payload_handler(query_user.first())
                                token = jwt_encode_handler(payload)
                                return JsonResponse(data={
                                    "errcode": 0,
                                    "msg": "登陆成功",
                                    "token": token,
                                    "name": user_data['name'],
                                    "avatar": user_data['avatar'],
                                })
                        except BaseException as e:
                            print(e)
                            logger.error('钉钉首次登录失败，获取信息出错。 原因:%s' % str(traceback.format_exc()))
                            return JsonResponse(data={
                                "errcode": 40004, "msg": "您的钉钉工作信息不完整, 请联系公司人事进行处理！", "data": "null"
                            })
                else:
                    logger.warning("您当前的邮箱%s不属于@pigs.com, 请解绑后联系公司人事进行邮箱绑定！" % str(email,))
                    return JsonResponse(data={
                        "errcode": 1009, "msg": "您当前的邮箱不属于@flybycloud, 请解绑后联系公司人事进行邮箱绑定！", "data": "null"
                    })
            else:
                logger.warning("您未绑定@pigs.com邮箱, 请联系公司人事进行邮箱绑定！")
                return JsonResponse(
                    data={"errcode": 1009, "msg": "您未绑定@pigs.com邮箱, 请联系公司人事进行邮箱绑定！", "data": "null"})

        except (TypeError, IndexError, ConnectionError) as e:
            logger.error('用户登录时系统出现异常, 异常原因: %s' % str(traceback.format_exc()))
            return JsonResponse(data={"errcode": 1010, "msg": "系统出错!", "data": "null"})
