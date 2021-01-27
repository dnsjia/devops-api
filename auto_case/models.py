from django.db import models
from api.models import UserInfo


class TestCase(models.Model):
    id = models.AutoField(primary_key=True)
    create_name = models.CharField(verbose_name='创建人', max_length=100)
    case_id = models.CharField(verbose_name='用例id', max_length=256, null=False)
    test_name = models.CharField(verbose_name='测试用例名称', max_length=40, null=False)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    ip = models.CharField(verbose_name='测试地址', max_length=100, null=False)
    browser = models.CharField(verbose_name='浏览器', max_length=32, null=False)
    version = models.CharField(verbose_name='版本', max_length=10, default="86")
    report_address = models.CharField(verbose_name='测试报告地址', max_length=100, null=False)
    loop = models.IntegerField(verbose_name='循环次数', default=1)
    import_address = models.CharField(verbose_name='测试用例地址', max_length=100, )
    run_models = models.CharField(verbose_name='运行的模块', max_length=15, default='全部')

    class Meta:
        db_table = 'test_case'
        verbose_name = '测试用例'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.test_name


class TestTask(models.Model):
    task_id = models.CharField(verbose_name='任务id', max_length=128)
    case_id = models.CharField(verbose_name='用例id', max_length=128)
    task_run_time = models.DateTimeField(verbose_name='任务执行时间', auto_now_add=True)
    task_run_done_time = models.DateTimeField(verbose_name='任务完成时间', null=True)
    total_time = models.CharField(verbose_name='任务执行耗时', max_length=128)

    class Meta:
        db_table = 'test_task'
        verbose_name = '用例执行任务'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.task_id


class TestCaseDetail(models.Model):
    task_id = models.CharField(verbose_name='任务id', max_length=128)
    logs = models.TextField(verbose_name='运行日志', max_length=2048)
    """
    0 success   用例成功个数
    1 failed    用例失败个数
    2 skip      用例跳过个数
    3 init      用例初始化过程
    """
    status = models.IntegerField(verbose_name='用例成功个数', default=3)

    class Meta:
        db_table = 'test_case_detail'
        verbose_name = '测试用例'
        verbose_name_plural = verbose_name