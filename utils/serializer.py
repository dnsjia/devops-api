#!/bin/env python3
# -*- coding: utf-8 -*-

"""
@Time: 2020/9/27 13:17
@Author: yu.jiang <safemonitor@outlook.com>
@License: Apache License
@File: serializer.py

"""

from rest_framework import serializers
from api.models import UserInfo, VirtualHost, Project, GrayType, TicketType, DeployTask, DeployStatusChart, \
    DatabaseRecord
from api.models import GrayDomain, AccountType, InnerAccount, State, Ticket, DeployRollBack


class UserInfoSerializer(serializers.ModelSerializer):
    """
    用户信息
    """

    class Meta:
        model = UserInfo
        fields = ["username", "email", "user_id", "mobile", "name", "sex", "position",
                  "avatar", "is_active", "last_login", "roles", "is_staff"
                  ]
        depth = 1


class NginxListModelSerializers(serializers.ModelSerializer):
    class Meta:
        model = VirtualHost
        fields = "__all__"
        # depth = 1


class ProjectModelSerializers(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"
        # depth = 1


class ApprovalListSerializer(serializers.ModelSerializer):
    """
    序列化部署单
    """
    project_title = serializers.CharField(source="project.title")
    status_cn = serializers.CharField(source="get_status_display")

    class Meta:
        model = DeployTask
        fields = '__all__'


class GrayDomainModelSerializers(serializers.ModelSerializer):
    class Meta:
        model = GrayDomain
        fields = "__all__"


class GrayModelSerializers(serializers.ModelSerializer):
    gray_domain = GrayDomainModelSerializers()

    class Meta:
        model = GrayType
        fields = "__all__"


class AccountModelSerializers(serializers.ModelSerializer):

    class Meta:
        model = AccountType
        fields = "__all__"


class AccountRecordrListModelSerializers(serializers.ModelSerializer):
    class Meta:
        model = InnerAccount
        fields = "__all__"


class TicketStateModeSerializers(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = "__all__"


class TicketTypeModelSerializers(serializers.ModelSerializer):
    class Meta:
        model = TicketType
        fields = "__all__"


class TicketRecordrListModelSerializers(serializers.ModelSerializer):
    state = TicketStateModeSerializers()
    ticket_type = TicketTypeModelSerializers()
    submit_account = serializers.CharField(source="submit_account.name")

    class Meta:
        model = Ticket
        fields = "__all__"


class DbAccountRecordrListModelSerializers(serializers.ModelSerializer):
    """
    db申请记录
    """
    class Meta:
        model = DatabaseRecord
        fields = "__all__"


class DeployRollBackModelSerializers(serializers.ModelSerializer):
    """
    序列化部署回滚表
    """
    class Meta:
        model = DeployRollBack
        fields = "__all__"


class DeployStatusChartModelSerializers(serializers.ModelSerializer):
    """
    部署状态图表api
    """
    class Meta:
        model = DeployStatusChart
        fields = "__all__"