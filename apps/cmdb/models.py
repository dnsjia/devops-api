#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.

from django.db import models
from django.utils import timezone

# Create your models here.

CHARGE_TYPE_CHOOICE = (
    ('PrePaid', '包年包月'),
    ('PostPaid', '按量付费')
)


class Server(models.Model):
    """
    服务器资产表
    """

    instance_id = models.CharField(max_length=32, verbose_name='实例id', primary_key=True)
    hostname = models.CharField(max_length=64, verbose_name='主机名', null=True, blank=True)
    private_ip = models.GenericIPAddressField(verbose_name='私网IP', null=True, blank=True)
    public_ip = models.GenericIPAddressField(verbose_name='公网IP', null=True, blank=True)
    mac_address = models.CharField(max_length=32, verbose_name='物理地址', null=True, blank=True)
    bandwidth = models.IntegerField(verbose_name='带宽M', null=True, blank=True, default=0)
    cpu = models.IntegerField(verbose_name='CPU核数', null=True, blank=True)
    memory = models.IntegerField(verbose_name='内存/GB', null=True, blank=True)
    os_name = models.CharField(max_length=64, verbose_name='操作系统', null=True, blank=True)
    NETWORK_TYPE_CHOICES = (
        ('vpc', '专有网络'),
        ('classic', '经典网络')
    )
    network_type = models.CharField(max_length=16, choices=NETWORK_TYPE_CHOICES, verbose_name='网络类型', null=True,
                                    blank=True)
    expired_time = models.CharField(max_length=32, verbose_name='过期时间', null=True, blank=True)
    image_id = models.CharField(max_length=128, verbose_name='系统镜像', null=True, blank=True)
    INSTANCE_STATUS_CHOICES = (
        ('Running', '运行中'),
        ('Stopped', '已停止')
    )
    status = models.CharField(max_length=32, choices=INSTANCE_STATUS_CHOICES, verbose_name='实例状态', default='Running')
    security_group = models.CharField(max_length=1024, verbose_name='安全组', null=True, blank=True)
    vpc_id = models.CharField(max_length=128, verbose_name='VPC', null=True, blank=True)
    switch_id = models.CharField(max_length=128, verbose_name='交换机', null=True, blank=True)
    serial_numer = models.CharField(max_length=128, verbose_name='SN序列号', null=True, blank=True)
    os_type = models.CharField(max_length=16, verbose_name='操作系统类型', null=True, blank=True)
    create_time = models.CharField(max_length=32, verbose_name='创建时间', null=True, blank=True)
    zone_id = models.CharField(max_length=32, verbose_name='可用区', null=True, blank=True)
    region_id = models.CharField(max_length=32, verbose_name='所属地域', null=True, blank=True)

    instance_charge_type = models.CharField(max_length=32, choices=CHARGE_TYPE_CHOOICE, verbose_name='实例计费方式',
                                            null=True, blank=True)
    BANDWIDTH_TYPE_CHOICES = (
        ('PayByTraffic', '按流量计费'),
        ('PayByBandwidth', '按带宽计费')
    )
    internet_charge_type = models.CharField(max_length=64, choices=BANDWIDTH_TYPE_CHOICES, verbose_name='带宽计费方式',
                                            null=True, blank=True)
    # specs = models.CharField(max_length=254, verbose_name='实例规格', null=True, blank=True)
    # salecycle = models.CharField(max_length=32, verbose_name='实例计费周期', null=True, blank=True)
    comment = models.CharField(max_length=64, verbose_name='实例描述', null=True, blank=True)
    POWER_STATE_CHOICES = (
        ('poweredOn', '打开'),
        ('poweredOff', '关闭')
    )
    power_state = models.CharField(max_length=32, verbose_name='电源', choices=POWER_STATE_CHOICES, default='poweredOn')
    CLOUD_TYPE_CHOICES = (
        ('aliyun', '阿里云'),
        ('server', '物理机'),
        ('virtual_machine', '虚拟机'),

    )
    cloud_type = models.CharField(max_length=32, verbose_name='类型', choices=CLOUD_TYPE_CHOICES, default='aliyun')

    class Meta:
        db_table = 'server'
        ordering = ['instance_id']
        verbose_name = '服务器信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.hostname

    @property
    def web_url(self):
        host = 'https://ecs.console.aliyun.com'
        url = f'{host}/#/server/{self.instance_id}/detail?regionId={self.region_id}'
        return url

    def to_dict(self):
        data = super().to_dict()
        print(data, 111)
        data['web_url'] = self.web_url
        return data


class CloudAK(models.Model):
    """
    阿里云ak
    """
    access_key = models.CharField(max_length=32, verbose_name='Access Key', null=True, blank=True, unique=True)
    access_secret = models.CharField(max_length=32, verbose_name='Access Secret', null=True, blank=True)
    active = models.BooleanField(verbose_name='启用状态', null=True, default=False)

    class Meta:
        db_table = 'cloud_ak'
        verbose_name = '阿里云AK'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.access_key


class Disk(models.Model):
    """
    磁盘
    """
    instance = models.ForeignKey('Server', verbose_name='实例ID', on_delete=models.SET_NULL, related_name='disk',
                                 null=True)
    disk_id = models.CharField(max_length=128, verbose_name='硬盘ID', null=True, blank=True)
    disk_name = models.CharField(max_length=64, verbose_name='硬盘名称', null=True, blank=True)
    CATEGORY_TYPE_CHOICES = (
        ('cloud', '普通云盘'),
        ('cloud_efficiency', '高效云盘'),
        ('cloud_ssd', 'SSD盘'),
        ('cloud_essd', 'ESSD云盘'),
    )
    category = models.CharField(max_length=32, verbose_name='硬盘类型', choices=CATEGORY_TYPE_CHOICES, default='cloud')
    device = models.CharField(max_length=128, verbose_name='设备名', null=True, blank=True)
    enable_auto_snapshot = models.BooleanField(verbose_name='自动快照策略', default=False)
    encrypted = models.BooleanField(verbose_name='是否加密', default=False)
    create_time = models.CharField(max_length=32, verbose_name='创建时间', null=True, blank=True)
    attached_time = models.CharField(max_length=32, verbose_name='挂载时间', null=True, blank=True)
    disk_charge_type = models.CharField(max_length=32, verbose_name='计费方式', choices=CHARGE_TYPE_CHOOICE)
    delete_with_instance = models.BooleanField(verbose_name='随实例释放', default=True)
    expired_time = models.CharField(max_length=32, verbose_name='过期时间', null=True, blank=True)
    description = models.CharField(max_length=128, verbose_name='硬盘描述', null=True, blank=True)
    size = models.IntegerField(verbose_name='硬盘大小/GiB', null=True, blank=True)
    DISK_STATUS_CHOICES = (
        ('In_use', '已挂载'),
        ('Available', '可用'),

    )
    status = models.CharField(max_length=32, verbose_name='状态', choices=DISK_STATUS_CHOICES)
    tags = models.CharField(max_length=128, verbose_name='标签', null=True, blank=True)
    serial_number = models.CharField(max_length=64, verbose_name='序列号', null=True, blank=True)
    DISK_TYPE_CHOICES = (
        ('system', '系统盘'),
        ('data', '数据盘')
    )
    type = models.CharField(max_length=32, verbose_name='盘类型', choices=DISK_TYPE_CHOICES)
    portable = models.BooleanField(verbose_name='是否可卸载', default=False)
    zone_id = models.CharField(max_length=32, verbose_name='所属可用区', null=True, blank=True)

    class Meta:
        db_table = 'disk'
        verbose_name = '硬盘管理'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.disk_id


class SecurityGroup(models.Model):
    """
    安全组
    """
    # instance_id = models.ManyToManyField('Server', verbose_name='服务器', null=True, blank=True)
    name = models.CharField(max_length=128, verbose_name='名称', null=True, blank=True)
    security_group = models.CharField(max_length=1024, verbose_name='安全组', null=True, blank=True)
    security_group_type = models.CharField(max_length=32, verbose_name='安全组类型', null=True, blank=True)
    desc = models.CharField(max_length=128, verbose_name='描述', null=True, blank=True)
    create_time = models.CharField(max_length=64, verbose_name='创建时间', null=True, blank=True)


class EcsAuthSSH(models.Model):
    """
    远程ssh 认证
    """
    AUTH_TYPE = (
        ('password', '密码认证'),
        ('key', '密钥认证')
    )
    type = models.CharField(max_length=32, verbose_name='认证方式', choices=AUTH_TYPE)
    username = models.CharField(verbose_name='用户名', max_length=64)
    password = models.CharField(verbose_name='密码', max_length=256, null=True, blank=True)
    key = models.TextField(verbose_name='密钥', null=True, blank=True)
    port = models.IntegerField(verbose_name='远程端口')
    SERVER_TYPE = (
        ('linux', 'linux'),
        ('windows', 'windows')
    )
    server_type = models.CharField(verbose_name='服务器类型', max_length=32, default='linux', choices=SERVER_TYPE)

    class Meta:
        db_table = 'ecs_ssh'
        verbose_name = 'SSH远程认证'
        verbose_name_plural = verbose_name


class AnsibleExecHistory(models.Model):
    """
    ansible 执行命令历史
    """
    COMMAND_TYPE = (
        ('shell', 'Shell命令'),
        ('win_shell', 'PowerShell命令'),
        ('playbook', 'Ansible PlayBook')
    )
    job_name = models.CharField(max_length=128, verbose_name='任务名称')
    command_type = models.CharField(max_length=16, verbose_name='命令类型', choices=COMMAND_TYPE)
    execute_user = models.CharField(max_length=32, verbose_name='执行用户', default='root')
    created_at = models.CharField(max_length=128, verbose_name='创建时间')
    host_count = models.IntegerField(verbose_name='机器数量')
    command_content = models.TextField(max_length=1024, verbose_name='命令内容')
    job_id = models.CharField(max_length=128, verbose_name='任务id')
    job_status = models.CharField(max_length=12, verbose_name='任务状态', default='PENDING')
    command_id = models.CharField(max_length=128, verbose_name='命令id')

    class Meta:
        db_table = 'ansible_execute_history'
        verbose_name = 'Ansible执行记录'
        verbose_name_plural = verbose_name
        ordering = ['-id']

    def __str__(self):
        return self.job_id


class AnsibleSyncFile(models.Model):
    """
    ansible 文件分发
    """
    execute_user = models.CharField(max_length=32, verbose_name='执行用户', default='root')
    created_at = models.CharField(max_length=128, verbose_name='创建时间')
    host_count = models.IntegerField(verbose_name='机器数量')
    job_id = models.CharField(max_length=128, verbose_name='任务id')
    job_status = models.CharField(max_length=12, verbose_name='任务状态', default='PENDING')
    command_id = models.CharField(max_length=128, verbose_name='命令id')
    dst_dir = models.CharField(max_length=512, verbose_name='目标路径')
    dst_filename = models.CharField(max_length=128, verbose_name='目标文件名称')
    src_filename = models.CharField(max_length=512, verbose_name='源文件名称')

    class Meta:
        db_table = 'ansible_sendfile_history'
        verbose_name = 'Ansible文件分发记录'
        verbose_name_plural = verbose_name
        ordering = ['-id']

    def __str__(self):
        return self.job_id


class AnsibleExecTemplate(models.Model):
    """
    1、输入命令内容
    3、 shell    4、powershell
    2、选择已保存的命令模板
    5、ansible playbook
   """
    template_name = models.CharField(max_length=128, verbose_name='模板名称')
    template_dsc = models.TextField(max_length=2048, verbose_name='描述')
    command_type = models.CharField(max_length=64, verbose_name='命令类型')
    template_dir = models.CharField(max_length=512, verbose_name='模板路径')
    created_at = models.CharField(max_length=128, verbose_name='创建时间')

    class Meta:
        db_table = 'ansible_execute_template'
        verbose_name = 'Ansible执行模板'
        verbose_name_plural = verbose_name
        ordering = ['-id']

    def __str__(self):
        return self.template_name
