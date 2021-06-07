#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.

import logging

from openpyxl import Workbook
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponse
from django.utils.translation import gettext_lazy

from apps.account.models import User

logger = logging.getLogger('default')


class ExportExcelMixin(object):
    """
    导出Excel
    """
    def export_as_excel(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='application/msexcel')
        response['Content-Disposition'] = f'attachment; filename={meta}.xlsx'
        wb = Workbook()
        ws = wb.active
        ws.append(field_names)
        for obj in queryset:
            for field in field_names:
                data = [f'{getattr(obj, field)}' for field in field_names]
            row = ws.append(data)

        wb.save(response)
        return response

    export_as_excel.short_description = '导出Excel'


@admin.register(User)
class UserProfileAdmin(UserAdmin, ExportExcelMixin):
    """继承并重写UserAdmin类, add_fieldsets添加字段在(django admin后台显示)
    重写原因: 解决后台添加用户, 密码显示明文
    """
    # 设置显示数据库中哪些字段
    list_display = ['username', 'name', 'email', 'mobile', 'position', 'hire_date', 'sex',
                    'is_active', 'is_staff', 'is_superuser', 'last_login', 'user_id', 'job_number', 'department']
    # filter_horizontal = ['department', 'groups']
    list_filter = ['position', 'is_active', 'is_staff', 'is_superuser']
    list_display_links = ['name', 'email']
    search_fields = ['username', 'name', 'mobile', 'email']
    actions = ['export_as_excel']
    filter_horizontal = ['groups']
    fieldsets = (
        (None, {'fields': ('username', 'password', 'name', 'email')}),
        (gettext_lazy('User Information'), {'fields': ('mobile', 'position', 'sex', 'hire_date', 'user_id', 'job_number', 'department')}),
        (gettext_lazy('Permissions'), {'fields': ('is_superuser', 'is_staff', 'is_active','groups', 'user_permissions')}),
        (gettext_lazy('Important dates'), {'fields': ('last_login', 'date_joined', 'roles')}),

    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'password1', 'password2', 'first_name', 'email',
            ),
        }),
        ('User Information', {
            'fields': (
                'mobile', 'position', 'sex', 'hire_date', 'user_id', 'job_number', 'department', 'name'
            ),

        }),
        ('Permissions', {
            'fields': (
                'is_superuser', 'is_staff', 'is_active', 'groups', 'user_permissions'
            )
        }),
    )
    list_per_page = 20
