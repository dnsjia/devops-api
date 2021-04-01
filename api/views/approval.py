#!/bin/env python3
# -*- coding: utf-8 -*-

"""
@Time: 2020/10/26 14:48
@Author: yu.jiang <safemonitor@outlook.com>
@License: Apache License
@File: approval.py

"""
import traceback
from django.db.models import Q
from django.http import JsonResponse
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from api.models import ApprovedGroup, DeployTask
from api.utils.authorization import MyAuthentication
from api.utils.permissions import MyPermission
from utils.rest_page import StandardResultsSetPagination
from utils.serializer import ApprovalListSerializer
import logging
logger = logging.getLogger('default')


class ApprovalSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    approval_name = serializers.CharField()

    class Meta:
        model = ApprovedGroup
        # fields = "__all__"
        fields = ["id", "approval_name"]


class ApprovalUserView(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        """
        获取审批人
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            user_id = request.user.user_id
            obj = ApprovedGroup.objects.filter(sponsor_id=user_id)
            ser = ApprovalSerializer(instance=obj, many=True, context={'request': request})
            return JsonResponse(data=ser.data, safe=False)

        except BaseException as e:
            logger.error('%s 请求获取审批人接口失败, 异常原因:%s' % (request.user.name, str(e)))
            logger.error('请求获取审批人接口失败, 异常原因: %s' % str(traceback.format_exc()))

            return JsonResponse(data={
                "errcode": "1006",
                "msg": "系统异常, 请刷新重试!",
                "data": e
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR, json_dumps_params={'ensure_ascii': False})


class ApprovalListView(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        """
        发布单审批列表
        :param request:
        :param args:
        :param kwargs:
        :return:
        """

        try:
            _status = request.GET.get('status', None)
            keywords = request.GET.get('keywords', None)
            if _status is not None:
                if _status == 'large':
                    query_deploy = DeployTask.objects.all().order_by('-id')
                    paginator = StandardResultsSetPagination()
                    deploy_list = paginator.paginate_queryset(query_deploy, self.request, view=self)
                    serializer_deploy_info = ApprovalListSerializer(deploy_list, many=True)
                    deploy_page = paginator.get_paginated_response(serializer_deploy_info.data)
                    return Response(deploy_page.data)

                else:
                    query_deploy = DeployTask.objects.filter(status=_status).order_by('-id')
                    paginator = StandardResultsSetPagination()
                    deploy_list = paginator.paginate_queryset(query_deploy, self.request, view=self)
                    serializer_deploy_info = ApprovalListSerializer(deploy_list, many=True)
                    deploy_page = paginator.get_paginated_response(serializer_deploy_info.data)
                    return Response(deploy_page.data)

            elif keywords is not None:
                query_deploy = DeployTask.objects.filter(Q(version__icontains=keywords)).order_by('-id')
                paginator = StandardResultsSetPagination()
                deploy_list = paginator.paginate_queryset(query_deploy, self.request, view=self)
                serializer_deploy_info = ApprovalListSerializer(deploy_list, many=True)
                deploy_page = paginator.get_paginated_response(serializer_deploy_info.data)
                return Response(deploy_page.data)

            else:
                query_deploy = DeployTask.objects.all().order_by('-id')
                paginator = StandardResultsSetPagination()
                deploy_list = paginator.paginate_queryset(query_deploy, self.request, view=self)
                serializer_deploy_info = ApprovalListSerializer(deploy_list, many=True)
                deploy_page = paginator.get_paginated_response(serializer_deploy_info.data)
                return Response(deploy_page.data)

        except BaseException as e:
            logger.error('%s 请求获取审批列表接口失败, 异常原因:%s' % (request.user.name, str(e)))
            logger.error('请求获取审批列表接口失败, 异常原因: %s' % str(traceback.format_exc()))
            return JsonResponse(data={
                "errcode": "1006",
                "msg": "系统异常, 请刷新重试!",
                "data": "null"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR, json_dumps_params={'ensure_ascii': False})


class ApprovalAllView(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        """
        统计部署单状态数量
        :param request:
        :param args:
        :param kwargs:
        :return:
        """

        try:
            # 待审核
            pending = DeployTask.objects.filter(status=1).count()
            # 待发布
            to_be_released = DeployTask.objects.filter(status=2).count()
            # 发布成功
            deploy_successful = DeployTask.objects.filter(status=4).count()
            # 发布异常
            deploy_failure = DeployTask.objects.filter(status=5).count()

            data = {
                "pending": pending,
                "to_be_released": to_be_released,
                "deploy_successful": deploy_successful,
                "deploy_failure": deploy_failure
            }
            return JsonResponse(data={"errcode": 0, "msg": "success", "data": data})

        except BaseException as e:
            logger.error(e)
            return JsonResponse(data={
                "errcode": "1006",
                "msg": "系统异常, 请刷新重试!",
                "data": "null"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR, json_dumps_params={'ensure_ascii': False})