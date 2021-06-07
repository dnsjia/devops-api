#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

from apps.rbac.models import Role


class User(AbstractUser):
    user_id = models.BigIntegerField(verbose_name='用户ID', unique=True, null=True, blank=True)
    mobile = models.CharField(max_length=11, verbose_name='手机号')
    name = models.CharField(max_length=32, verbose_name='姓名')
    job_number = models.CharField(max_length=32, verbose_name='工号', null=True, blank=True)
    position = models.CharField(max_length=64, null=True, verbose_name='职位信息', blank=True)
    hire_date = models.DateTimeField(verbose_name='入职时间', null=True)
    avatar = models.URLField(verbose_name='用户头像', null=True, blank=True)
    sex = models.CharField(max_length=8, verbose_name='性别', choices=(('man', '男'), ('women', '女')), default='man')
    roles = models.ManyToManyField(Role, verbose_name='角色', blank=True)
    department = models.CharField(max_length=128, verbose_name='部门', null=True, blank=True)

    class Meta:
        db_table = 'users'
        verbose_name = '用户信息'
        verbose_name_plural = verbose_name
        ordering = ['-id']

    def __str__(self):
        return self.name


class History(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ip = models.CharField(max_length=50)
    type = models.CharField(max_length=20, default='email', verbose_name='登录类型：邮箱、钉钉')  # email, ding
    created_at = models.CharField(max_length=20, default=timezone.now())

    class Meta:
        db_table = 'login_history'
        ordering = ['-id']


