from django.test import TestCase

# Create your tests here.

# for k,v in old:
# 	instance_id = v.get('instance_id')
# 	new_data = new_dict['instance_id']
#
# print(new_dict)


# for update in update_server:
#     temp = []
#     insert_instance = next((item for item in ecs_results_data if item['instance_id'] == update), None)
#     for key, value in insert_instance.items():
#         old_value = getattr(server_all_dict[update], key)
#         if value == old_value:
#             # 没有发生变化, 什么都不做
#             continue
#         msg = "ecs的{}, 由{}变更成了{}".format(key, old_value, value)
#         temp.append(msg)
#
#         setattr(server_all_dict[update], key, value)
#         # getattr(db_disk_dict[slot], key)  # ---> 每一项：数据库中值， 每一项：新增值 ---> value
#
#         print(key, value, getattr(server_all_dict[update], key))
#
#     if temp:
#         # 如果temp不为空,说明字段发生了变化
#         server_all_dict[update].save()
#         row = "[更新硬盘] 槽位：{}, 更新的内容:{}".format(update, ';'.join(temp))
#         record_str_list.append(row)

# Server.objects.update_or_create(defaults=ecs_instance, instance_id=ecs_instance.get('instance_id'))


# server_queryset_all = Server.objects.values()
# new_dict = {}
# for new_ecs_value in ecs_results_data:
#     instance_id = new_ecs_value.get(new_ecs_value)
#     new_dict[new_ecs_value] = new_ecs_value
#
# for old_server in server_queryset_all:
#     print(type(old_server))
    # for k, v in old_server:
    #     instance_id = v.get(new_ecs_value)
    #     new_data = new_dict[new_ecs_value]
    #     print(new_dict, new_data)
# for k, v in server_queryset_all:
#     instance_id = v.get(instance_id)
#     new_data = new_dict[instance_id]
#     if v != new_data:
#         print(new_dict)

# for old_server in [entry for entry in server_queryset_all]:
#     update = update_server.items() - old_server.items()
#     if update:
#         print('资产发生变化: {}'.format(update_server))

# Server.objects.update_or_create(defaults=update_server, instance_id=update_server.get('instance_id'))

# 　update_server = server_new_results & old_server_all
# for update in update_server:
#     temp = []
#     insert_instance = next((item for item in ecs_results_data if item['instance_id'] == update), None)
#     for key, value in insert_instance.items():
#         old_value = getattr(server_all_dict[update], key)
#         if value == old_value:
#             # 没有发生变化, 什么都不做
#             continue
#         msg = "ecs的{}, 由{}变更成了{}".format(key, old_value, value)
#         temp.append(msg)
#
#         setattr(server_all_dict[update], key, value)
#         # getattr(db_disk_dict[slot], key)  # ---> 每一项：数据库中值， 每一项：新增值 ---> value
#
#         print(key, value, getattr(server_all_dict[update], key))
#
#     if temp:
#         # 如果temp不为空,说明字段发生了变化
#         server_all_dict[update].save()
#         row = "[更新硬盘] 槽位：{}, 更新的内容:{}".format(update, ';'.join(temp))
#         record_str_list.append(row)

# Server.objects.update_or_create(defaults=ecs_instance, instance_id=ecs_instance.get('instance_id'))

import datetime


origin_date_str= "2021-08-27T16:00Z"
utc_date = datetime.datetime.strptime(origin_date_str, "%Y-%m-%dT%H:%MZ")
local_date = utc_date + datetime.timedelta(hours=8)
local_date_str = datetime.datetime.strftime(local_date ,'%Y-%m-%d %H:%M')
print(local_date_str )