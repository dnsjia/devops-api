#!/bin/env python3
# -*- coding: utf-8 -*-

"""
@Time: 2020/10/30 22:26
@Author: yu.jiang <safemonitor@outlook.com>
@License: Apache License
@File: dingtalk_notice.py

"""
import json
import requests
from decouple import config
import logging
import traceback
logger = logging.getLogger('default')


class DingTalkSendMsg:
    @classmethod
    def get_token(self):
        """
        获取调用企业接口凭证。可通过 appkey、appsecret 或 corpid、corpsecret 换取access_token
        :return:
        """
        app_key = config('D_APP_KEY')
        app_secret = config('D_APP_SECRET')

        url = f'https://oapi.dingtalk.com/gettoken?appkey={app_key}&appsecret={app_secret}'
        try:
            res = requests.get(url=url).json()
            if res.get('errcode') == 0:
                access_token = res.get('access_token')
                return access_token
            else:
                logger.error("获取企业凭证失败，%s" % res)
        except BaseException as e:
            logger.error(e)
            logger.error('获取企业凭证失败: %s' % str(traceback.format_exc()))

    @classmethod
    def send_msg(self, title, msg, user_id):
        """
        发送钉钉工作通知消息
        :param title: 标题
        :param msg: 内容， markdown 格式
        :param user_id: 用户user_id  多个用户以list=[]
        :return:
        """

        access_token = DingTalkSendMsg.get_token()
        dingtalk_url = f'https://oapi.dingtalk.com/topapi/message/corpconversation/asyncsend_v2?access_token={access_token}'

        data = {
            "agent_id":config('D_AGENT_ID'),
            "msg":{
                "markdown":{
                    "title": str(title),
                    "text": str(msg)
                },
                "msgtype":"markdown"
            },
            "userid_list":str(user_id)
        }
        try:
            res = requests.post(url=dingtalk_url, data=json.dumps(data)).json()
            if res.get('errcode') != 0:
                logger.error('发送钉钉工作通知消息异常，%s' %(str(res)))
            logger.info('发送钉钉工作通知消息完成，请求body:{%s}' %(str(data)))

        except BaseException as e:
            logger.error(e)
            logger.error('发送钉钉工作通知消息异常: %s' % str(traceback.format_exc()))