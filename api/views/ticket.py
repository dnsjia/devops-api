#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
@Author: 风哥
@Mail: gujiwork@outlook.com
@File:ticket.py
@Time:2020/10/26 14:39
"""
import json
import time
import traceback
from api.utils.dingtalk_notice import DingTalkSendMsg
from api.utils.permissions import MyPermission
from utils.code import RandCode
from django.http import JsonResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from api.models import Ticket, TicketType, UserInfo
from api.utils.authorization import MyAuthentication
from utils.rest_page import StandardResultsSetPagination
from utils.serializer import TicketRecordrListModelSerializers, TicketTypeModelSerializers
from api.tasks import send_dingtalk_group
import logging
logger = logging.getLogger('default')


class TicketRecordView(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        """
        获取工单
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            if request.user.is_superuser:
                obj_ticket_list = Ticket.objects.all()
                paginator = StandardResultsSetPagination()
                page_ticket_list = paginator.paginate_queryset(obj_ticket_list, self.request, view=self)
                serializer_ticket_info = TicketRecordrListModelSerializers(page_ticket_list, many=True)
                page_ticket_record = paginator.get_paginated_response(serializer_ticket_info.data)
                return Response(page_ticket_record.data)
            else:
                obj_ticket_list = Ticket.objects.filter(submit_account=request.user.user_id)
                paginator = StandardResultsSetPagination()
                page_ticket_list = paginator.paginate_queryset(obj_ticket_list, self.request, view=self)
                serializer_ticket_info = TicketRecordrListModelSerializers(page_ticket_list, many=True)
                page_ticket_record = paginator.get_paginated_response(serializer_ticket_info.data)
                return Response(page_ticket_record.data)

        except BaseException as e:
            logger.error("系统异常: %s" % str(traceback.format_exc()))
            return JsonResponse(data={
                "errcode": "1006",
                "msg": "系统异常, 请刷新重试!",
                "data": "null"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR, json_dumps_params={'ensure_ascii': False})


class TicketDetailView(APIView):
    def get(self, request, *args, **kwargs):
        ticket_id = request.GET.get('ticketId', None)

        if ticket_id is None:
            return JsonResponse(data={'errcode': 404, 'msg': '获取工单错误！'})
        try:
            if request.user.is_superuser:
                obj_ticket_list = Ticket.objects.filter(ticket_number=ticket_id)
                paginator = StandardResultsSetPagination()
                page_ticket_list = paginator.paginate_queryset(obj_ticket_list, self.request, view=self)
                serializer_ticket_info = TicketRecordrListModelSerializers(page_ticket_list, many=True)
                page_ticket_record = paginator.get_paginated_response(serializer_ticket_info.data)
                return Response(page_ticket_record.data)

            else:
                obj_ticket_list = Ticket.objects.filter(ticket_number=ticket_id)
                account = Ticket.objects.get(ticket_number=ticket_id)
                if int(request.user.user_id) != int(account.submit_account_id):
                    return JsonResponse(data={'errcode': 404, 'msg': '获取工单错误！'})
                paginator = StandardResultsSetPagination()
                page_ticket_list = paginator.paginate_queryset(obj_ticket_list, self.request, view=self)
                serializer_ticket_info = TicketRecordrListModelSerializers(page_ticket_list, many=True)
                page_ticket_record = paginator.get_paginated_response(serializer_ticket_info.data)
                return Response(page_ticket_record.data)

        except BaseException:
            logger.error("查看工单详情出错: %s" % str(traceback.format_exc()))
            return JsonResponse(data={
                "errcode": "1006",
                "msg": "系统异常, 请刷新重试!",
                "data": "null"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR, json_dumps_params={'ensure_ascii': False})


class TicketTypelView(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        """
        工单类型
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            obj_data = TicketType.objects.all()
            paginator = StandardResultsSetPagination()
            page_ticket_type_list = paginator.paginate_queryset(obj_data, self.request, view=self)
            serializer_ticket_type_info = TicketTypeModelSerializers(page_ticket_type_list, many=True)
            page_ticket = paginator.get_paginated_response(serializer_ticket_type_info.data)
            return Response(page_ticket.data)

        except BaseException:
            logger.error("请求工单类型出错: %s" % str(traceback.format_exc()))
            return JsonResponse(data={
                "errcode": "1006",
                "msg": "系统异常, 请刷新重试!",
                "data": "null"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR, json_dumps_params={'ensure_ascii': False})


class TicketView(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def post(self, request, *args, **kwargs):
        """
        提交工单
        :param request:
        :param args:
        :param kwargs:
        :return:
        """

        try:
            data = json.loads(request.body, encoding='utf-8')['params']
            user_id = UserInfo.objects.filter(name=request.user.name).first()
            ticket_files = data.get('ticketFile')
            if not ticket_files or ticket_files is None:
                ticket_file = ''
            else:
                ticket_file = ticket_files['data']

            ticket_id = TicketType.objects.filter(ticket_type=data.get('ticketType')).first()
            ticket_data = {
                'ticket_number': RandCode.ticket_number_code(),
                'name': data.get('ticketTitle'),
                'submit_account_id': user_id.user_id,
                'problem_content': data.get('ticketDesc'),
                'ticket_type_id': ticket_id.id,
                'state_id': 3,
                'ticket_files': json.dumps(ticket_file),

            }

            Ticket.objects.create(**ticket_data).save()
            logger.info("工单提交成功, 提交人: %s" % str(request.user.name))
            send_dingtalk_group.delay("您有一条工单待处理！\n %s" % data.get('ticketTitle'))
            return JsonResponse(data={'errcode': 0, 'msg':'工单提交成功'})

        except BaseException:
            logger.error("工单提交失败, 原因: %s" % str(traceback.format_exc()))
            return JsonResponse(data={'errcode': 500, 'msg':'工单提交异常！'})
