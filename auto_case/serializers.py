#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : serializers.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2021/1/10
# @Desc  :
from rest_framework import serializers
from auto_case.models import TestTask, TestCase, TestCaseDetail


class TestCaseSerializerAll(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = TestCase
        extra_kwargs = {'id': {'required': False}}


class TestCaseTaskSerializerOther(serializers.ModelSerializer):
    class Meta:
        fields = ['id','task_id','case_id','task_run_time','task_run_done_time','total_time']
        model = TestTask
        extra_kwargs = {'id': {'required': False}}
        # depth=1


class TestCaseTaskLogsSerializerOther(serializers.ModelSerializer):
    class Meta:
        fields = ['id','task_id','logs','status']
        model = TestCaseDetail
        extra_kwargs = {'id': {'required': False}}

