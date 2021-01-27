#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : case_notice.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2021/1/22
# @Desc  :
import json
import traceback
import requests
import logging

logger = logging.getLogger('default')


class CaseDoneNotice(object):

    @classmethod
    def notice(self, data, at_user=None):
        """
        用例运行完成后，发送钉钉群组通知
        :param at_user:
        :param data: 接受数据
        :return:
        """
        develop_group_notice_url = 'https://oapi.dingtalk.com/robot/send?access_token={dingding token}'
        headers = {
            'Content-Type': 'application/json;charset=utf-8',
        }

        json_text = {
            "msgtype": "text",
            "at": {
                "atMobiles":
                    at_user,
                "isAtAll": False  # 为True表示@所有人
            },
            "text": {
                "content": data
            }
        }
        try:
            rsp = requests.post(develop_group_notice_url, json.dumps(json_text), headers=headers).content
            print(rsp)
        except Exception as e:
            logger.error('钉钉消息发送失败, 异常原因: %s' % str(traceback.format_exc()), e)
