#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.

from django.db import models


class Menu(models.Model):
    """
    菜单
    """
    name = models.CharField(verbose_name='菜单名称', max_length=32, unique=True)
    icon = models.CharField(verbose_name='图标', max_length=32, blank=True)
    path = models.CharField(verbose_name='链接地址', help_text='如果有子菜单，不需要填写该字段', blank=True, max_length=100)
    is_active = models.BooleanField(verbose_name='激活状态', default=True)
    sort = models.IntegerField(verbose_name='排序标记', blank=True)
    pid = models.ForeignKey("self", verbose_name="上级菜单", null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = '菜单'
        verbose_name_plural = verbose_name
        ordering = ['sort']

    def __str__(self):
        return self.name


class Permission(models.Model):
    """
    权限
    """
    name = models.CharField(verbose_name='权限名称', max_length=32, unique=True)
    path = models.CharField(verbose_name='含正则的URL', blank=True, max_length=128)
    method = models.CharField(verbose_name='方法', max_length=16, default='GET')
    pid = models.ForeignKey('self', verbose_name='上级权限', null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = '权限'
        verbose_name_plural = verbose_name
        ordering = ['id']

    def __str__(self):
        return self.name


class Role(models.Model):
    """
    角色
    """
    name = models.CharField(verbose_name='角色名称', max_length=32, unique=True)
    permissions = models.ManyToManyField('Permission', verbose_name='权限', blank=True)
    menus = models.ManyToManyField('Menu', verbose_name='菜单', blank=True)
    desc = models.CharField(verbose_name='描述', max_length=50, blank=True)

    class Meta:
        verbose_name = '角色'
        verbose_name_plural = verbose_name
        ordering = ['id']

    def __str__(self):
        return self.name
