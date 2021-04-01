from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy
# Register your models here.
from api.models import InnerAccount, DatabaseRecord, GrayDomain
from api.models import Project
from api.models import Ticket
from api.models import  DeployTask
from api.models import ApprovedGroup
from api.models import Server
from api.models import UserInfo

from django.http import HttpResponse
from openpyxl import Workbook
import logging

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


@admin.register(InnerAccount)
class InnerAccount(admin.ModelAdmin, ExportExcelMixin):
    list_display = ('name', 'account_name', 'account_zh_desc', 'status', 'created_time')
    list_filter = ['account_zh_desc', 'status', 'created_time']  # 过滤器
    search_fields = ['account_name', 'name']  # 搜索字段
    actions = ['export_as_excel']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin, ExportExcelMixin):
    list_display = ['id', 'title', 'project_env', 'repo', 'description', 'created_time']
    list_display_links = ['title', 'repo']
    list_filter = ['project_env', 'created_time']
    search_fields = ['title', 'project_env']
    actions = ['export_as_excel']


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin, ExportExcelMixin):
    # 设置显示数据库中哪些字段
    list_display = ['id', 'name', 'ticket_type', 'submit_account', 'ticket_files', 'state', 'created_time']
    list_display_links = ['name']
    list_filter = ['ticket_type', 'state', 'created_time']
    search_fields = ['title', 'ticket_originator', 'ticket_files', 'submit_account']
    actions = ['export_as_excel']

    def save_model(self, request, obj, form, change):
        if form.is_valid():
            super().save_model(request, obj, form, change)
            # form 方法,  保存save()  校验is_valid()  获取数据cleaned_data
            # 工单状态==3已完成, 发送email通知
            if form.cleaned_data['state'] == 3:
                logger.info('工单处理完成, 开始发送异步通知')


@admin.register(DeployTask)
class DeployTaskAdmin(admin.ModelAdmin, ExportExcelMixin):
    list_display = ['id', 'task_id', 'title', 'version', 'approval_user', 'status', 'test_report', 'submit_people',
                    'develop_user', 'dingtalk_notice', 'online_time']
    list_display_links = ['task_id']
    list_filter = ['submit_people', 'status', 'created_time', 'approval_user']
    search_fields = ['submit_people', 'project', 'task_id', 'title', 'test_report', 'approval_user']
    actions = ['export_as_excel']


@admin.register(ApprovedGroup)
class ApprovedGroupAdmin(admin.ModelAdmin):
    list_display = ['id', 'approval_name', 'sponsor_id']

    def sponsor_id(self, obj):
        """ 重写外键显示字段"""
        return obj.sponsor
    list_display_links = ['approval_name']


@admin.register(Server)
class ServerAdmin(admin.ModelAdmin, ExportExcelMixin):
    list_display = ['id', 'instance_id', 'hostname', 'internet_ip', 'intranet_ip', 'os_platform', 'os_kernel', 'regions',
                    'create_time']
    list_display_links = ['instance_id', 'internet_ip']
    list_filter = ['os_platform', 'regions', 'create_time']
    search_fields = ['instance_id', 'hostname', 'internet_ip', 'intranet_ip']
    actions = ['export_as_excel']


@admin.register(DatabaseRecord)
class DbAdmin(admin.ModelAdmin, ExportExcelMixin):
    list_display = ['id', 'applicant', 'account', 'env_name', 'database_name', 'permissions', 'desc', 'status',
                    'create_time']
    list_display_links = ['account', 'desc']
    list_filter = ['env_name', 'status', 'database_name']
    search_fields = ['account', 'applicant']
    actions = ['export_as_excel']


@admin.register(UserInfo)
class UserProfileAdmin(UserAdmin, ExportExcelMixin):
    """继承并重写UserAdmin类, add_fieldsets添加字段在(django admin后台显示)
    重写原因: 解决后台添加用户, 密码显示明文
    """
    # 设置显示数据库中哪些字段
    list_display = ['name', 'position', 'email', 'mobile', 'position', 'hire_date', 'sex',
                    'is_active', 'is_staff', 'is_superuser', 'last_login']
    # filter_horizontal = ['department', 'groups']
    list_filter = ['position', 'is_active','is_staff', 'is_superuser']
    search_fields = ['username', 'name', 'mobile', 'email']
    actions = ['export_as_excel']
    filter_horizontal = ['groups']
    fieldsets = (
        (None, {'fields': ('username', 'password', 'first_name', 'last_name', 'email')}),
        (gettext_lazy('User Information'), {'fields': ('mobile', 'position', 'sex', 'hire_date')}),
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
                'mobile', 'position', 'sex', 'hire_date'
            ),

        }),
        ('Permissions', {
            'fields': (
                'is_superuser', 'is_staff', 'is_active', 'groups', 'user_permissions'
            )
        }),
    )
    list_per_page = 20


@admin.register(GrayDomain)
class GrayDomainAdmin(admin.ModelAdmin):
    list_display = ['id', 'domain_name']
    list_display_links = ['domain_name']
