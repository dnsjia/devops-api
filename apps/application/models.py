#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


from django.db import models

# Create your models here.


class Diagnosis(models.Model):
    name = models.CharField(max_length=64, verbose_name='应用名称', null=True, blank=True)
    ip = models.GenericIPAddressField(verbose_name='应用IP', null=True, blank=True)
    user_name = models.CharField(max_length=32, verbose_name='安装用户', null=True, blank=True)
    is_active = models.BooleanField(verbose_name='是否在线', null=True, blank=True, default=0)
    process_name = models.CharField(verbose_name='进程名', null=True, blank=True, max_length=32)
    is_container = models.BooleanField(verbose_name='是否容器', null=True, blank=True, default=0)

    class Meta:
        db_table = 'diagnosis'
        verbose_name = '应用诊断'
        verbose_name_plural = verbose_name
        ordering = ['-id']

    def __str__(self):
        return self.name
