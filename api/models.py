from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from rbac.models import Role


# Create your models here.
class ApprovedGroup(models.Model):
    """审批表
    """
    id = models.AutoField(primary_key=True)
    approval_name = models.CharField(verbose_name='审批人', max_length=64)
    sponsor = models.ForeignKey(verbose_name='提交人', to='UserInfo', related_name='sponsor_user',
                                on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = 'approved_users'
        verbose_name = '审批设置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.approval_name


class UserInfo(AbstractUser):
    user_id = models.BigIntegerField(verbose_name='用户ID', primary_key=True, unique=True)
    mobile = models.CharField(max_length=11, verbose_name='手机号')
    name = models.CharField(max_length=32, verbose_name='姓名')
    job_number = models.CharField(max_length=32, verbose_name='工号')
    position = models.CharField(max_length=64, verbose_name='职位信息', null=True, blank=True)
    hire_date = models.DateTimeField(verbose_name='入职时间')
    avatar = models.URLField(verbose_name='用户头像', null=True, blank=True)
    sex_choices = (
        ('man', '男'),
        ('women', '女')
    )
    sex = models.CharField(max_length=8, verbose_name='性别', choices=sex_choices)
    roles = models.ManyToManyField('rbac.Role', verbose_name='角色', blank=True)

    class Meta:
        db_table = 'user_info'
        verbose_name = '用户信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class UserToken(models.Model):
    """
    用户Token
    """
    user = models.OneToOneField(to='UserInfo', on_delete=models.SET_NULL, null=True)
    token = models.CharField(max_length=512, default='', verbose_name='用户TOKEN')
    expire = models.DateTimeField(verbose_name='过期时间', null=True)

    class Meta:
        db_table = 'user_token'
        verbose_name = '用户token'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.token


class Server(models.Model):
    """
    服务器表
    """
    id = models.AutoField(primary_key=True)
    instance_id = models.CharField(verbose_name='实例ID', max_length=256, null=True, blank=True)
    hostname = models.CharField(verbose_name='主机名', max_length=32)
    status = models.IntegerField(choices=((0, '在线'),
                                          (1, '离线'),
                                          (2, '停用')),
                                 default=0,
                                 verbose_name='主机状态')
    internet_ip = models.GenericIPAddressField(verbose_name='公网IP', null=True, blank=True)
    intranet_ip = models.GenericIPAddressField(verbose_name='私网IP', null=True, blank=True)
    port = models.SmallIntegerField(verbose_name='ssh端口', default=22)
    mac_address = models.CharField(max_length=128, verbose_name='物理地址', null=True, blank=True)
    cpu = models.CharField(max_length=128, verbose_name='CPU型号', null=True, blank=True)
    cpu_num = models.SmallIntegerField(verbose_name='CPU数量', null=True, default=1)
    memory = models.CharField(verbose_name='内存大小', max_length=128, null=True, blank=True)
    disk = models.CharField(max_length=256, verbose_name='磁盘容量', null=True, blank=True)
    bandwidth = models.SmallIntegerField(verbose_name='带宽', default='0')
    os_platform = models.CharField(max_length=64, verbose_name='操作系统', default='Centos7', null=True, blank=True)
    os_kernel = models.CharField(max_length=128, verbose_name='系统内核', null=True, blank=True)
    regions = models.CharField(max_length=64, verbose_name='地域', null=True, blank=True)
    sn = models.CharField(max_length=128, verbose_name='SN序列号', null=True, blank=True)
    description = models.TextField(max_length=256, verbose_name='备注', null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='添加时间')

    class Meta:
        db_table = 'server_info'
        verbose_name = '服务器信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.hostname


class VirtualHost(models.Model):
    """"
    虚拟主机
    """
    internet_port = models.IntegerField(verbose_name='外网端口', unique=True)
    upstream_name = models.CharField(max_length=256, verbose_name='后端名称')
    forward_address = models.GenericIPAddressField(max_length=128, verbose_name='转发地址')
    port = models.IntegerField(verbose_name='端口')
    remarks = models.CharField(max_length=256, verbose_name='备注', null=True)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    creator_name = models.CharField(verbose_name='创建人', max_length=64)

    class Meta:
        db_table = "virtual_host"
        verbose_name = "虚拟主机"
        verbose_name_plural = verbose_name
        ordering = ["-id"]


class Project(models.Model):
    """
    项目表
    """
    id = models.AutoField(primary_key=True)
    title = models.CharField(verbose_name='项目名称', max_length=64)
    repo = models.CharField(verbose_name='仓库地址', max_length=256, null=True, blank=True)
    env_choices = (
        ('test', '测试环境'),
        ('uat', '验收环境'),
        ('pre', '预发环境'),
        ('prod', '生产环境')
    )
    app_choices = ((0, '容器化应用'), (1, '普通应用'))
    is_container = models.IntegerField(verbose_name='是否容器化, 0容器,1普通', choices=app_choices, default=1)
    project_env = models.CharField(verbose_name='环境名称', max_length=16, choices=env_choices, default='test')
    path = models.CharField(verbose_name='线上路径', max_length=256, default='/data/webapps/')
    servers = models.ManyToManyField(verbose_name='关联服务器', to='Server', blank=True)
    description = models.CharField(verbose_name='描述信息', max_length=256, null=True, blank=True)
    created_time = models.DateTimeField(verbose_name='添加时间', default=timezone.now)

    class Meta:
        db_table = 'project_info'
        verbose_name = '项目信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return "%s-%s" % (self.title, self.get_project_env_display())


class InnerAccount(models.Model):
    name = models.CharField(verbose_name='申请人', null=True, max_length=32)
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='申请时间')
    reasons = models.CharField(verbose_name='申请原因', max_length=1024, null=True)
    account_type = models.IntegerField(verbose_name='账号类型')
    account_name = models.CharField(verbose_name='账号名称', max_length=256, null=True)
    status = models.IntegerField(verbose_name='0同意,1拒绝,2审核中', choices=((0, "同意"), (1, "拒绝"), (2, "审核中")), default=2)
    account_zh_desc = models.CharField(verbose_name='账号中文描述', max_length=256)

    class Meta:
        db_table = 'inner_account'
        verbose_name = '帐号申请记录'
        verbose_name_plural = verbose_name
        ordering = ['-id']

    def __str__(self):
        return self.name


class AccountType(models.Model):
    account_types = ()

    id = models.IntegerField(primary_key=True)
    account_type = models.CharField(verbose_name='帐号类型', null=True, max_length=128, choices=account_types)

    class Meta:
        db_table = 'account_type'
        verbose_name = '帐号类型'
        verbose_name_plural = verbose_name


class DeployTask(models.Model):
    """发布任务单
    """
    id = models.AutoField(primary_key=True)
    task_id = models.CharField(verbose_name='任务标识', max_length=64)  # tmc-manage-v100-2020050911
    project = models.ForeignKey(verbose_name='项目环境', to='Project', related_name='project', on_delete=models.SET_NULL,
                                null=True)
    title = models.CharField(max_length=256, verbose_name='发布原因')
    version = models.CharField(verbose_name='上线版本', max_length=256)

    status_choices = (
        (1, '待审批'),
        (2, '已通过'),
        (3, '部署中'),
        (4, '部署成功'),
        (5, '部署失败'),
        (6, '已拒绝'),
    )
    status = models.IntegerField(verbose_name='状态', choices=status_choices, default=1)
    before_comment = models.TextField(verbose_name='上线说明', null=True, blank=True)
    dingtalk_notice = models.BooleanField(default=True, verbose_name='钉钉通知')
    approval_user = models.CharField(verbose_name='审批人', max_length=64)
    test_report = models.FileField(verbose_name='测试报告', max_length=256, null=True)
    develop_user = models.CharField(verbose_name='研发人员', max_length=64)
    online_time = models.DateTimeField(verbose_name='应用上线时间', null=True, blank=True)
    created_time = models.DateTimeField(verbose_name='提交时间', auto_now_add=True)
    submit_people = models.CharField(verbose_name='提交人', max_length=32)
    submit_user = models.ForeignKey(to='UserInfo', related_name='submit_user_id', on_delete=models.SET_NULL,
                                    verbose_name='提交用户ID', null=True)
    refuse_msg = models.CharField(verbose_name='拒绝原因', max_length=256, null=True, blank=True)
    deploy_env = models.CharField(verbose_name='环境信息(test,prod,uat,dev)', max_length=32)
    deploy_type = models.CharField(verbose_name='部署类型(INC, CONTAINER)', max_length=32)
    original_file_name = models.CharField(verbose_name='原始文件名', max_length=256, null=True, blank=True)

    class Meta:
        db_table = 'deploy_task'
        verbose_name = '部署任务单'
        verbose_name_plural = verbose_name
        ordering = ['-id']

    def __str__(self):
        return self.task_id


class GrayDomain(models.Model):
    domain_name = models.CharField(verbose_name='域名', max_length=64, unique=True)

    class Meta:
        db_table = 'gray_manage'
        verbose_name = "灰度管理"
        verbose_name_plural = verbose_name
        ordering = ['-id']


class GrayType(models.Model):
    gray_domain = models.ForeignKey(to='GrayDomain', on_delete=models.CASCADE)
    gray_type = models.CharField(verbose_name='灰度类型', max_length=64)
    created_time = models.DateTimeField(verbose_name='创建时间', default=timezone.now)
    match_content = models.CharField(verbose_name='匹配内容', max_length=256)
    match_key = models.CharField(verbose_name='匹配KEY', max_length=256)
    match_value = models.CharField(verbose_name='匹配VALUE', max_length=256)
    creator_name = models.CharField(verbose_name='创建人', max_length=64)

    class Meta:
        db_table = 'gray_rules'
        verbose_name = "灰度规则"
        verbose_name_plural = verbose_name
        ordering = ['-id']


class State(models.Model):
    """
    状态记录
    """
    state_types = {
        0: '已关闭',
        1: '处理中',
        2: '待处理',
        3: '已完成',
    }
    state_type = models.CharField(max_length=1, choices=tuple(state_types.items()), verbose_name='状态类型')

    class Meta:
        db_table = 'ticket_state'
        verbose_name = "工单状态"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.get_state_type_display()


class TicketType(models.Model):
    """
    工单问题类型
    """
    ticket_types = {
        1: '配置变更',
        2: '域名申请',
        3: '故障提交',
        4: '数据处理',
        5: '其它'

    }
    ticket_type = models.CharField(verbose_name='帐号类型', null=True, max_length=128, choices=tuple(ticket_types.items()))

    class Meta:
        db_table = 'ticket_type'
        verbose_name = "工单类型"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.get_ticket_type_display()


class Ticket(models.Model):
    ticket_number = models.CharField(verbose_name='工单编号', max_length=16, unique=True)
    name = models.CharField(verbose_name='工单标题', max_length=112)
    submit_account = models.ForeignKey(to='UserInfo', verbose_name='工单发起人', related_name='submit_account',
                                       on_delete=models.CASCADE)
    assign_to = models.CharField(max_length=24, verbose_name='工单处理人', null=True, blank=True)
    problem_content = models.TextField(verbose_name='工单内容')
    result_desc = models.TextField(verbose_name='处理结果', blank=True, null=True)
    created_time = models.DateTimeField(verbose_name='提交时间', default=timezone.now)
    completion_time = models.DateTimeField(verbose_name='处理完成时间', default=timezone.now, null=True)
    state = models.ForeignKey(to='State', on_delete=models.CASCADE, related_name='ticket_state_to', verbose_name='当前状态')
    ticket_type = models.ForeignKey(to='TicketType', related_name='ticket_type_to', verbose_name='工单类型',
                                    on_delete=models.CASCADE)
    ticket_files = models.TextField(verbose_name='工单附件', max_length=512, null=True)

    class Meta:
        db_table = 'ticket'
        verbose_name = "工单记录"
        verbose_name_plural = verbose_name
        ordering = ['-id']


class DeployLogs(models.Model):
    id = models.AutoField(primary_key=True)
    task_id = models.CharField(max_length=128, verbose_name='任务编号', null=True, blank=True)
    project_id = models.SmallIntegerField(verbose_name='项目ID', null=True, blank=True)
    message = models.CharField(max_length=128, verbose_name='操作记录', null=True, blank=True)
    audit_time = models.DateTimeField(verbose_name='审计时间', auto_now_add=True)
    progress = models.SmallIntegerField(verbose_name='部署进度', null=True, blank=True, default=0)
    status = models.SmallIntegerField(verbose_name='状态', null=True, blank=True)

    class Meta:
        db_table = 'deploy_logs'
        verbose_name = '部署单操作日志'
        verbose_name_plural = verbose_name
        ordering = ['id']

    def __str__(self):
        return self.task_id


class BuildHistory(models.Model):
    """
    构建历史
    """
    build_id = models.IntegerField(verbose_name="构建编号")
    task_id = models.CharField(verbose_name='任务编号', max_length=256)
    app_name = models.CharField(max_length=128, verbose_name='项目名称')

    class Meta:
        db_table = 'build_history'
        verbose_name = "构建历史"
        verbose_name_plural = verbose_name


class SyncJobHistory(models.Model):
    """
    集群同步记录
    """
    sync_id = models.IntegerField(verbose_name='同步任务ID')
    sync_project = models.CharField(max_length=128, verbose_name='同步任务名称')
    sync_code_type = models.CharField(max_length=64, verbose_name='同步代码类型')
    off_slb = models.BooleanField(verbose_name='是否下线负载均衡')
    is_restart_tomcat = models.BooleanField(verbose_name='是否重启Tomcat')
    created_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    build_status = models.CharField(verbose_name='构建状态', max_length=64)

    class Meta:
        db_table = 'sync_job_history'
        verbose_name = "集群同步历史"
        verbose_name_plural = verbose_name


class DeployRollBack(models.Model):
    """
    部署回滚表
    """

    project_name = models.CharField(max_length=256, verbose_name='项目名称', null=True, blank=True)
    package_name = models.CharField(max_length=128, verbose_name='回滚版本', null=True, blank=True)
    backup_type = models.CharField(verbose_name='备份类型', max_length=16, null=True, blank=True)
    backup_time = models.DateTimeField(verbose_name='备份时间', auto_now=True)
    files_md5 = models.CharField(max_length=512, verbose_name='文件md5', null=True, blank=True, default='null')
    namespace = models.CharField(max_length=128, verbose_name='命名空间', null=True, blank=True)
    registry = models.CharField(max_length=2048, verbose_name='镜像仓库', null=True, blank=True)

    class Meta:
        db_table = 'deploy_rollback'
        verbose_name = '版本回滚'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.project_name


class DeployStatusChart(models.Model):
    """
    一周部署状态图表
    """
    id = models.AutoField(primary_key=True)
    days = models.CharField(max_length=32, verbose_name='日期', null=True, blank=True)
    deploy_status = models.CharField(max_length=16, verbose_name='部署状态', null=True, blank=True)
    count = models.SmallIntegerField(verbose_name='次数', null=True, blank=True)

    class Meta:
        db_table = 'deploy_status_chart'
        verbose_name = '状态图表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.days


class DatabaseRecord(models.Model):
    """
    数据库申请记录
    """
    id = models.AutoField(primary_key=True)
    status = models.IntegerField(choices=((0,'已同意'),(1,'已拒绝'),(2, '审核中')), default=2)
    env_name = models.CharField(verbose_name='环境名称', max_length=64)
    database_name = models.CharField(verbose_name='库名', max_length=64)
    desc = models.CharField(verbose_name='申请原因', max_length=512)
    permissions = models.CharField(verbose_name='权限', max_length=128)
    applicant = models.CharField(verbose_name='申请人', max_length=64)
    account = models.CharField(verbose_name='帐号名称', max_length=128)
    create_time = models.DateTimeField(verbose_name='申请时间', auto_now=True)

    class Meta:
        db_table = 'database_record'
        verbose_name = '数据库记录'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.status