import traceback
from django.db.models import Q
from django.http import JsonResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
import json
from api.models import DatabaseRecord
from api.utils.authorization import MyAuthentication
import logging
import ast
from decouple import config
from api.utils.permissions import MyPermission
from utils.rest_page import StandardResultsSetPagination
from utils.serializer import DbAccountRecordrListModelSerializers
from utils.code import RandCode
import pymysql
from pymysql.err import OperationalError
mydb = pymysql.connect(host=config('MYSQL_HOST'),
                       user=config('MYSQL_USER'),
                       passwd=config('MYSQL_PASS'))
from api.tasks import send_deploy_email
logger = logging.getLogger('default')


class DatabaseView(APIView):

    authentication_classes = [MyAuthentication]
    permission_classes = [MyPermission, ]

    def get(self, request, *args, **kwargs):
        """
        列出db申请账号
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            if request.user.is_superuser:
                obj_db_account_list = DatabaseRecord.objects.filter(Q(status=2)).order_by('-id')[:8]
                paginator = StandardResultsSetPagination()
                page_db_account_list = paginator.paginate_queryset(obj_db_account_list, self.request, view=self)
                serializer_db_account_info = DbAccountRecordrListModelSerializers(page_db_account_list, many=True)
                page_db_account_record = paginator.get_paginated_response(serializer_db_account_info.data)
                return Response(page_db_account_record.data)
            else:
                obj_db_account_list = DatabaseRecord.objects.filter(Q(applicant=request.user.name)).order_by('-id')[:8]
                paginator = StandardResultsSetPagination()
                page_db_account_list = paginator.paginate_queryset(obj_db_account_list, self.request, view=self)
                serializer_db_account_info = DbAccountRecordrListModelSerializers(page_db_account_list, many=True)
                page_db_account_record = paginator.get_paginated_response(serializer_db_account_info.data)
                return Response(page_db_account_record.data)

        except BaseException as e:
            logger.error('系统出现异常: %s' % str(traceback.format_exc()))
            return JsonResponse(data={
                "errcode": "1006",
                "msg": "系统异常, 请刷新重试!",
                "data": "null"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR, json_dumps_params={'ensure_ascii': False})

    def post(self, request, *args, **kwargs):
        """
        申请数据库权限
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            data = json.loads(request.body, encoding='utf-8')['params']
            db_data = {}
            db_data['env_name'] = data.get('env')
            db_data['database_name'] = data.get('databaseName')
            db_data['desc'] = data.get('desc')
            db_data['permissions'] = data.get('permissions')
            db_data['applicant'] = request.user.name
            db_data['account'] = request.user.username

            obj = DatabaseRecord.objects.filter(account=db_data['account'], database_name=db_data['database_name'], status=2).first()
            '''根据提交中的帐号和数据库db名称去数据库查询待审批的状态 2，如果申请的权限和数据库里面的权限相等，权限无变化则提示正在审批中'''
            if obj is not None:
                logger.info(db_data['permissions'], '你申请的权限')
                if str(obj.permissions) == str(db_data['permissions']):
                    return JsonResponse(data={'errcode': 1000, 'msg': '您申请的权限正在审批中,请耐心等待！'})
                else:
                    '''如果权限不相等，则更新权限'''
                    DatabaseRecord.objects.filter(account=db_data['account'], database_name=db_data['database_name'], status=2).update(**db_data)
                    return JsonResponse(data={'errcode': 0, 'msg': '你已提交更新权限,请耐心等待管理员审批！'})
            else:
                '''如果状态不为2， 创建新的审批记录'''
                DatabaseRecord.objects.create(**db_data)
                return JsonResponse(data={'errcode': 0, 'msg': '提交成功,请耐心等待管理员审批！'})
        except BaseException as e:
            logger.error('申请数据库权限异常：{%s}' % str(traceback.format_exc()))
            return JsonResponse(data={'errcode': 500, 'msg': '申请权限出错,请稍后再试！'})

    def put(self, request, *args, **kwargs):
        """
        更新数据库权限， 同意或拒绝
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        if not request.user.is_superuser:
            return JsonResponse({
                "errcode": 403,
                "msg": "您当前无权操作！",
                "data": []},json_dumps_params={'ensure_ascii': False})

        try:
            global data
            data = request.data['params']
        except BaseException as e:
            return JsonResponse(data={'errcode': 500, 'msg': '获取参数异常！'})

        if str(data.get('status')) == 'refuse':
            account_status = DatabaseRecord.objects.filter(id=data.get('id')).first()
            account_status.status = 1
            account_status.save()
            return JsonResponse(data={'errcode': 0, 'msg': '已拒绝该用户的申请'})
        elif str(data.get('status')) == 'agree':
            '''
             select,insert,update,delete,create,drop,index,alter,grant,references,reload,shutdown,process,file
             创建用户并授权
             mysql>grant select,insert,update,delete,create,drop,index on student.* to test@localhost identified by 'A1b2c3#!@';
             查看授权
             mysql> show grants for test@localhost;
             移除权限
             mysql> revoke insert,update on student.* from test@localhost;
             刷新权限
             flush privileges;
             
             https://www.cnblogs.com/felix-h/p/11072743.html
             '''
            obj = DatabaseRecord.objects.filter(id=data.get('id')).first()
            permissions = ['select', 'insert', 'update', 'delete']
            db_permissions = ast.literal_eval(obj.permissions)
            not_pms = [y for y in (permissions + db_permissions) if y not in db_permissions]
            mydb = pymysql.connect(host=config('MYSQL_HOST'),
                                   user=config('MYSQL_USER'),
                                   passwd=config('MYSQL_PASS'))
            cursor = mydb.cursor()
            cursor.execute("select * from mysql.user")
            results = cursor.fetchall()

            in_account = []
            for account in results:
                # 数据库中所有的用户
                in_account.append(account[1])
            logger.info("数据库查询出的帐号：%s" % in_account)
            if obj.account in in_account:
                logger.info('用户: %s已存在！' % obj.account)
                logger.info("申请的权限是：%s" % db_permissions)
                # 先移除已存在的权限，在更新新的权限
                if 'update' not in db_permissions:
                    try:
                        add_pms = ['create', 'index', 'alter']
                        new_pms = ','.join(not_pms + add_pms)
                        remove_pms = f"revoke {new_pms} on {obj.database_name}.* from {obj.account}@'%'"
                        logger.info("移除用户权限：SQL语句：%s" % remove_pms )

                        try:
                            cursor.execute(remove_pms)
                            cursor.execute("flush privileges")
                            cursor.close()
                        except OperationalError:
                            # 出现这种错误， 授权了A库，B库没有任何授权， 此时移除B库权限时就出抛错
                            # 更新权限
                            update_pms = ','.join(db_permissions)
                            sql = f"grant {update_pms} ON {obj.database_name}.* to {obj.account}@'%';"
                            logger.info("更新用户权限：%s" % (sql))
                            cursor.execute(sql)
                            cursor.execute("flush privileges")
                            cursor.close()
                            obj.status = 0
                            obj.save()
                            return JsonResponse(data={'errcode': 0, 'msg': '权限更新成功'})
                        # 更新权限
                        update_pms = ','.join(db_permissions)
                        sql = f"grant {update_pms} ON {obj.database_name}.* to {obj.account}@'%';"
                        logger.info("更新用户权限：%s" % sql)
                        cursor.execute(sql)
                        cursor.execute("flush privileges")
                        cursor.close()
                        obj.status = 0
                        obj.save()
                        return JsonResponse(data={'errcode': 0, 'msg': '权限更新成功'})

                    except BaseException as e:
                        logger.error('权限更新异常, 异常原因: %s' % str(traceback.format_exc()), e)
                        return JsonResponse(data={'errcode': 500, 'msg': '权限更新异常'})

                else:
                    try:
                        # 如果有update 直接更新权限
                        add_pms = ['create', 'index', 'alter']
                        update_pms = ','.join(db_permissions + add_pms)
                        sql = f"grant {update_pms} ON {obj.database_name}.* to {obj.account}@'%';"
                        logger.info("更新用户权限：%s" % sql)
                        cursor.execute(sql)
                        cursor.execute("flush privileges")
                        cursor.close()
                        obj.status = 0
                        obj.save()
                        return JsonResponse(data={'errcode': 0, 'msg': '权限更新成功'})
                    except BaseException as e:
                        logger.error('权限更新异常, 异常原因: %s' % str(traceback.format_exc()), e)
                        return JsonResponse(data={'errcode': 500, 'msg': '权限更新异常'})

            else:
                password = RandCode.random_password()
                logger.info("mysql用户不存在，开始创建用户：%s, 密码：%s" %(obj.account, password,) )
                logger.info("申请的权限是：%s" %(db_permissions,))
                # 如果有勾选update 权限，则给用户授权 create index alter process
                add_pms = ['create', 'index', 'alter']
                new_pms = ','.join(db_permissions + add_pms)
                title = '帐号开通提醒'
                msg = '您申请的帐号已经开通， 用户名：%s, 请妥善保管（%s）密码！' % (str(obj.account), str(password))
                msg_en = 'Your account has been opened. User name: %s Please keep your password! (%s)' % (
                    str(obj.account),
                    str(password)
                )
                url = 'mysql.svc.pigs.com'

                if 'update' in db_permissions:
                    try:
                        create_sql = f"grant {new_pms} on {obj.database_name}.* to {obj.account}@'%' identified by '{password}'"
                        logger.info("用户选择了update, SQL语句%s" % create_sql)
                        # TODO 用户创建成功，通知
                        cursor.execute(create_sql)
                        cursor.execute("flush privileges")
                        cursor.close()
                        obj.status = 0
                        obj.save()
                        logger.info(msg + '开始发送异步通知')
                        send_deploy_email.delay(str(obj.account) + '@pigs.com', obj.applicant, title, msg, msg_en, url, subject=title)
                        return JsonResponse(data={'errcode': 0, 'msg': '用户创建成功'})
                    except BaseException as e:
                        logger.error('权限更新异常, 异常原因: %s' % str(traceback.format_exc()), e)
                        return JsonResponse(data={'errcode': 500, 'msg': '权限更新异常'})
                else:
                    try:
                        pms = ','.join(db_permissions)
                        create_sql = f"grant {pms} on {obj.database_name}.* to {obj.account}@'%' identified by '{password}'"
                        logger.info("用户没有选择update, SQL语句：%s" % create_sql)
                        # TODO 用户创建成功，通知
                        cursor.execute(create_sql)
                        cursor.execute("flush privileges")
                        cursor.close()
                        obj.status = 0
                        obj.save()
                        logger.info(msg + '开始发送异步通知')
                        send_deploy_email.delay(str(obj.account) + '@pigs.com', obj.applicant, title, msg, msg_en, url, subject=title)
                        return JsonResponse(data={'errcode': 0, 'msg': '用户创建成功'})
                    except BaseException as e:
                        logger.error('权限更新异常, 异常原因: %s' % str(traceback.format_exc()), e)
                        return JsonResponse(data={'errcode': 500, 'msg': '权限更新异常'})
