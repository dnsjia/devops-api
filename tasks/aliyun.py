#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
@Time: 2021/4/14 0014 下午 12:18
@Author: micheng. <safemonitor@outlook.com>
@File: aliyun.py
"""

from celery import shared_task
from django.db import transaction

from controller.get_all_ecs import SyncECS
from apps.cmdb.models import CloudAK, Server, Disk


@shared_task
def sync_ecs():
    """定时更新ECS资产信息"""

    ak = CloudAK.objects.filter(active=True).values('access_key', 'access_secret')
    if not ak.exists():
        print("ECS资产同步异常, 您可能未正确配置阿里云AK、或后台阿里云AK被未启用。")
        return False

    with transaction.atomic():
        try:
            aliyun = SyncECS(ak[0]['access_key'], ak[0]['access_secret'])
            aliyun.get_region()
            ecs_results_data = aliyun.get_ecs()

            server_new_results = set()
            server_queryset_all = Server.objects.all()
            server_all_dict = {row.instance_id: row for row in server_queryset_all}
            old_server_all = set(server_all_dict)

            for instance in ecs_results_data:
                """ 将接口返回的数据取出instance_id字段存入空集合中"""
                server_new_results.add(instance.get('instance_id'))

            ecs_instance = server_new_results - old_server_all
            print('正在同步阿里云ECS实例信息, 此过程大约耗时10~30s...')
            for instance_id in ecs_instance:
                """ 新增服务器资产, 从ecs_results_data列表中获取指定的dict"""

                instance = next((item for item in ecs_results_data if item['instance_id'] == instance_id), None)
                Server.objects.create(**instance)
                print('本次插入数据库ECS实例={}'.format(instance))

            # TODO: 资产更新, 遍历接口列表中的dict===数据库的数据。 如果字段发生了变化则更新
            # 删除资产
            remove_server = old_server_all - server_new_results
            Server.objects.filter(instance_id__in=remove_server, cloud_type='aliyun').delete()
            if remove_server:
                print("数据库中ECS实例数据与接口中不一致, 开始[删除ECS实例] instance：{}".format(','.join(remove_server)))

        except BaseException as e:
            print('发生了错误={}'.format(e))
            raise sync_ecs.retry(exc=e, countdown=300, max_retries=3)


@shared_task
def sync_cloud_disk():
    print("开始同步云硬盘....")
    # 获取所有区域下的磁盘信息
    # print(ecs.get_disk())
    ak = CloudAK.objects.filter(active=True).values('access_key', 'access_secret')
    if not ak.exists():
        print("ECS资产同步异常, 您可能未正确配置阿里云AK、或后台阿里云AK被未启用。")
        return False

    with transaction.atomic():
        try:
            aliyun = SyncECS(ak[0]['access_key'], ak[0]['access_secret'])
            aliyun.get_region()
            disk_results = aliyun.get_disk()

            disk_dict = {}
            for disk in disk_results:
                """ 将接口返回的数据取出instance_id字段存入空集合中"""
                if disk is not None:
                    disk_dict['instance_id'] = disk['InstanceId']
                    disk_dict['disk_id'] = disk['DiskId']
                    disk_dict['disk_name'] = disk['DiskName']
                    disk_dict['category'] = disk['Category']
                    disk_dict['device'] = disk['Device']
                    disk_dict['enable_auto_snapshot'] = disk['EnableAutoSnapshot']
                    disk_dict['encrypted'] = disk['Encrypted']
                    disk_dict['create_time'] = disk['CreationTime']
                    disk_dict['attached_time'] = disk['AttachedTime']
                    disk_dict['disk_charge_type'] = disk['DiskChargeType']
                    disk_dict['delete_with_instance'] = disk['DeleteWithInstance']
                    disk_dict['expired_time'] = disk['ExpiredTime']
                    disk_dict['description'] = disk['Description']
                    disk_dict['size'] = disk['Size']
                    disk_dict['status'] = disk['Status']
                    disk_dict['tags'] = disk['Tags']
                    disk_dict['serial_number'] = disk['SerialNumber']
                    disk_dict['type'] = disk['Type']
                    disk_dict['portable'] = disk['Portable']
                    disk_dict['zone_id'] = disk['ZoneId']

                    Disk.objects.update_or_create(defaults=disk_dict, disk_id=disk_dict.get('disk_id'))

            print('已完成硬盘同步...')

        except Exception as e:
            raise sync_cloud_disk.retry(exc=e, countdown=300, max_retries=3)
