#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
# @File  : http_response.py
# @Author: 往事随风
# @Email: gujiwork@outlook.com
# @Date  : 2021/4/13
# @Desc  :
"""

from rest_framework.response import Response


class APIResponse(Response):
    """
    自定义Response返回数据：
    return APIResponse(data={"name":'11111111'},request_id='11111111')
    return APIResponse(data={"name":'11111111'})
    return APIResponse(errcode='101', errmsg='错误',data={"name":'11111111'}, header={})
    """
    def __init__(self, errcode=0, errmsg=None, data=None, status=None, headers=None, **kwargs):
        dic = {'errcode': errcode, 'errmsg': errmsg}
        if data:
            dic = {'errcode': errcode, 'errmsg': errmsg, 'data': data}
        dic.update(kwargs)
        super().__init__(data=dic, status=status, headers=headers)

