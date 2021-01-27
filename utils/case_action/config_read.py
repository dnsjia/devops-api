#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : config_read.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2021/1/11
# @Desc  :
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 用例与用例的运行间隔时间 单位:S
CASE_TIME = 1
# 元素查找等待时间 单位:S
ELEMENT_TIME = 30
# 谷歌浏览器版本
BROWSER_VERSION = '85'

'''通过BASE_DIR获取项目所在的路径（相对路径），然后根据项目路径获取其他文件的相对路径'''

# action(公共文件)路径
ACTION_PATH = os.path.join(BASE_DIR, 'action\\')
# drivers(驱动文件)路径
DRIVERS_PATH = os.path.join(BASE_DIR, 'drivers\\')
# excel_template(用例模板)路径
EXCEL_TEMPLATE_PATH = os.path.join(BASE_DIR, 'excel_template\\')
# report(报告文件)路径
REPORT_PATH = os.path.join(BASE_DIR, 'report\\')
# screenshots(截图文件)路径
SCREENSHOTS_PATH = os.path.join(BASE_DIR, 'screenshots\\')

'''EXCEL测试用例部分字段的列号'''

# 用例编号
TEST_CASE_NUM = 2
# 用例工作表
TEST_CASE_SHEET = 3
# 是否执行
TEST_CASE_IS_IMPL_EMENT = 6
# 执行结束时间
TEST_CASE_END_TIME = 7
# 结果
TEST_CASE_RESULT = 8

'''EXCEL用例步骤部分字段的列号'''

# 用例编号
TEST_STEP_NUM = 1
# 工作表
TEST_STEP_MOUDLE = 2
# 预置条件
TEST_STEP_PRE_SET = 3
# 用例标题
TEST_STEO_TITLE = 4
# 预期结果
TEST_STEP_EXPECT = 5
# 测试步骤描述
TEST_STEP_DESCRIBE = 6
# 关键字
TEST_STEP_KEYWORD = 7
# 定位方式
TEST_STEP_LOCATION = 8
# 表达式
TEST_STEP_LOCATOR = 9
# 操作值
TEST_STEP_VALUE = 10
# 测试执行时间
TEST_STEP_END_TIME = 11
# 测试结果
TEST_STEP_RESULT = 12
# 错误信息
TEST_STEP_ERROR = 17
# 截图
TEST_STEP_PICTURE = 18

