#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
# @File  : utils.py.py
# @Author: 往事随风
# @Email: gujiwork@outlook.com
# @Date  : 2021/5/13
# @Desc  :
"""

# import os
# import uuid
# import django
# from django.conf import settings
# django.setup()
#
# def get_ansible_task_log_path(task_id):
#     return get_task_log_path(settings.LOG_PATH, task_id, level=3)
#
#
# def get_task_log_path(base_path, task_id, level=2):
#     task_id = str(task_id)
#     try:
#         uuid.UUID(task_id)
#     except:
#         BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#         PROJECT_DIR = os.path.dirname(BASE_DIR)
#         return os.path.join(PROJECT_DIR, 'data', 'caution.txt')
#
#     rel_path = os.path.join(*task_id[:level], task_id + '.log')
#     path = os.path.join(base_path, rel_path)
#     os.makedirs(os.path.dirname(path), exist_ok=True)
#     return path
#
#
#
