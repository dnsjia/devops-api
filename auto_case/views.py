import traceback
from django_redis import get_redis_connection
from utils.code import RandCode
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
from api.utils.authorization import MyAuthentication
from api.utils.permissions import MyPermission
from auto_case.serializers import TestCaseSerializerAll, TestCaseTaskSerializerOther, TestCaseTaskLogsSerializerOther
from auto_case.testcase import RunnerTestCase
from api.tasks import run_case_test
import logging
from auto_case.models import TestCase, TestCaseDetail, TestTask
from utils.rest_page import StandardResultsSetPagination
conn_redis = get_redis_connection('default')
logger = logging.getLogger('default')


class TestCaseList(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def get(self, request):
        # 获取所有测试用例
        queryset = TestCase.objects.all().order_by('-id')
        paginator = StandardResultsSetPagination()
        case_list = paginator.paginate_queryset(queryset, self.request, view=self)
        serializer_case_info = TestCaseSerializerAll(case_list, many=True)
        case_page = paginator.get_paginated_response(serializer_case_info.data)
        return Response(case_page.data)


class TestCaseAdd(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def post(self, request):
        with transaction.atomic():
            save_id = transaction.savepoint()
            logger.info('新增用例信息：%s' % str(request.data))
            data = request.data['params']
            case_obj = TestCase.objects.filter(test_name=data['case_name']).first()
            if case_obj:
                return Response(data={'errcode': 4001, 'msg': '用例名称已存在！'})
            try:
                case_id_str = str(data['case_file']).split('.')[0].split('-')
                case_id = ''
                orm_data = {
                    'create_name': request.user.name,
                    'case_id': case_id.join(case_id_str),
                    'test_name': data['case_name'],
                    'ip': data['case_url'],
                    'browser': data['case_browser'],
                    'loop': data['case_loop'],
                    'import_address': data['case_file'],
                    'run_models': data['case_module']

                }
                TestCase.objects.create(**orm_data)
                return Response(data={'errcode': 0, 'msg': '新增用例成功'})
            except Exception as e:
                transaction.savepoint_rollback(save_id)
                logger.error('添加用例失败，错误原因：%s' % str(traceback.format_exc()), e)
                return Response(data={'errcode': 9999, 'msg': '新增用例失败'})


class TestRunner(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def post(self, request):
        # 运行EXCEL测试用用例
        data = request.data['params']
        data['ip'] = data.get('url')
        del data['url']
        data['task_id'] = RandCode.uuid1_hex()
        logger.info('用户：%s, 运行用例, data={%s}' % (request.user.name, data))
        # RunnerTestCase().runner_beautiful_report()
        task_data = {
            'task_id': data['task_id'],
            'case_id': data['case_id']
        }
        LOCK_CASE_ID = data['case_id'] + "_lock"
        lock_value = conn_redis.get(LOCK_CASE_ID)
        if lock_value is not None and lock_value.decode('utf-8') == "True":
            logger.warning("上一个任务正在进行中, 请等待任务结束后再试. 操作人: %s" % request.user.name)
            return Response(data={"errcode": 5001, "msg": "上一个任务正在进行中, 请稍后再试! ", "data": "null"})
        else:
            conn_redis.set(LOCK_CASE_ID, 'True')
            logger.info("没有获取到锁, 进行加锁{%s} 防止多次执行测试任务" % data['case_id'])
        TestTask.objects.create(**task_data)
        # 调用异步任务运行测试任务
        async_result = run_case_test.delay(data)
        logger.info('已开始运行测试任务, 异步任务返回ID: %s, 状态: %s' % (str(async_result.id), str(async_result.state)))
        # 如果不需要异步任务，把下面的注释打开
        # RunnerTestCase('test_case', data).run_report()
        return Response({'errcode': 0, 'msg': '测试用例后台运行中,请稍后查看！'})


class TestDetailById(generics.RetrieveAPIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    queryset = TestCase.objects.all()
    serializer_class = TestCaseSerializerAll


class TestCaseTask(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def get(self, request):
        # 获取所有测试用例任务
        case_id = request.query_params['caseId']
        queryset = TestTask.objects.filter(case_id=case_id).order_by('-id')
        paginator = StandardResultsSetPagination()
        case_list = paginator.paginate_queryset(queryset, self.request, view=self)
        serializer_case_info = TestCaseTaskSerializerOther(case_list, many=True)
        case_page = paginator.get_paginated_response(serializer_case_info.data)
        return Response(case_page.data)


class TestCaseTaskLogs(APIView):
    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def post(self, request):
        # 获取用例任务日志
        data = request.data['params']
        queryset = TestCaseDetail.objects.filter(task_id=data.get('task_id'))
        success = TestCaseDetail.objects.filter(task_id=data.get('task_id'), status=0).count()
        failed = TestCaseDetail.objects.filter(task_id=data.get('task_id'), status=1).count()
        skip = TestCaseDetail.objects.filter(task_id=data.get('task_id'), status=2).count()
        logger.info('用例执行状态统计, 成功：%d, 失败：%d, 跳过：%d' %(success, failed, skip))
        response = {'errcode': 0, 'msg': 'success', 'total': '', 'data': []}
        ret = TestCaseTaskLogsSerializerOther(queryset, many=True)
        response['data'] = ret.data
        response['total'] = len(ret.data)
        response['case_success'] = success
        response['case_failed'] = failed
        response['case_skip'] = skip
        return Response(response)
