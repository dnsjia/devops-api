#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : page_action.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2021/1/10
# @Desc  :
import traceback
from selenium.webdriver.common.keys import Keys
from utils.case_action.case_logs import CaseInsertLogs
from utils.case_action.object_map import ObjectMap
from utils.case_action.dir_and_time import DirAndTime
from utils.case_action.wait_unit import WaitUnit
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
# from selenium.common.exceptions import *   # 导入所有异常类
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains  # 鼠标操作
from utils.case_action.config_read import BROWSER_VERSION, DRIVERS_PATH, SCREENSHOTS_PATH
import time
import os
import win32gui
import win32con
import xlrd
# import constants
import logging
from auto_case.models import TestTask
logger = logging.getLogger('default')


class PageAction(object):
    def __init__(self, data):
        self.data = data
        self.byDic = {
            'id': By.ID,
            'name': By.NAME,
            'css': By.CSS_SELECTOR,
            'link_text': By.LINK_TEXT,
            'xpath': By.XPATH,
            'class': By.CLASS_NAME,
            'tag': By.TAG_NAME,
            'link': By.PARTIAL_LINK_TEXT
        }
        self.task_obj = TestTask.objects.filter(task_id=self.data.get('task_id')).first()

    def open_browser(self, browser, version):
        """
        获取浏览器类型
        :param browser: 火狐、谷歌
        :param version: 仅谷歌浏览器需要版本
        """
        browser_version = {
            '70': '70.0.3538.97',
            '71': '71.0.3578.137',
            '72': '72.0.3626.6',
            '73': '73.0.3683.68',
            '74': '74.0.3729.6',
            '75': '75.0.3770.1',
            '76': '76.0.3809.126',
            '77': '77.0.3865.40',
            '78': '78.0.3904.11',
            '79': '79.0.3945.16',
            '85': '85.0.4183.87',
            '86': '86.0.4240.22',
            '87': '87.0.4280.88',
        }
        # TODO 设置浏览器版本
        version = browser_version.get(version, browser_version.get(BROWSER_VERSION))
        msg = "选择的浏览器为: %s浏览器" % browser
        CaseInsertLogs.test_case_logs(self.task_obj.task_id, msg, 3)

        if browser == 'Google Chrome':
            print("选择的浏览器为: %s浏览器" % browser,)
            path = DRIVERS_PATH + 'chrome\\' + version + '\\chromedriver.exe'
            if version is not None:
                path = path
                logger.info(path, '驱动目录')
            else:
                logger.warning('浏览器版本不符合，请检查浏览器版本')
                return
            option = Options()
            option.add_experimental_option('w3c', False)
            option.add_argument('--start-maximized')
            self.driver = webdriver.Chrome(executable_path=path, options=option)
            msg = '启动谷歌浏览器'
            CaseInsertLogs.test_case_logs(self.task_obj.task_id, msg, 3)
            logger.info(msg)
            print(msg)
        elif browser == 'FireFox':
            path = DRIVERS_PATH + 'firefox\\' + 'geckodriver.exe'
            self.driver = webdriver.Firefox(executable_path=path)
            self.driver.maximize_window()
            msg = '启动火狐浏览器'
            CaseInsertLogs.test_case_logs(self.task_obj.task_id, msg, 3)
            logger.info(msg)
            print(msg)
        else:
            # 驱动创建完成后，等待创建实例对象
            WaitUnit(self.driver)

    def quit_browser(self):
        msg = '退出浏览器'
        logger.info(msg)
        print(msg)
        CaseInsertLogs.test_case_logs(self.task_obj.task_id, msg, 3)
        self.driver.quit()

    def close_browser(self):
        msg = '关闭当前页面'
        logger.info(msg)
        print(msg)
        CaseInsertLogs.test_case_logs(self.task_obj.task_id, msg, 3)
        self.driver.close()

    def back(self):
        # 退回浏览器上一个页面
        if self.driver.current_url == 'data:,':
            msg = '返回到: %s' % self.driver.current_url
            logger.info(msg)
            print(msg)
            CaseInsertLogs.test_case_logs(self.task_obj.task_id, msg, 3)
            self.driver.back()
        else:
            msg = '已经是第一个页面,无法在后退了'
            logger.info(msg)
            print(msg)
            CaseInsertLogs.test_case_logs(self.task_obj.task_id, msg, 3)
            return

    def forward(self):
        # 前进浏览器上一个页面
        msg = '前进到: %s' % self.driver.current_url
        logger.info(msg)
        print(msg)
        CaseInsertLogs.test_case_logs(self.task_obj.task_id, msg, 3)
        self.driver.forward()

    def refresh(self):
        # 刷新浏览器
        msg = '刷新浏览器'
        logger.info(msg)
        print(msg)
        self.driver.refresh()
        CaseInsertLogs.test_case_logs(self.task_obj.task_id, msg, 3)

    def js_scroll_top(self):
        # 滚动到顶部
        js = "window.scrollTo(0,0)"
        self.driver.execute_script(js)

    def js_scroll_end(self):
        # 滚动到底部
        js = "window.scrollTo(0,document.body.scrollHeight)"
        self.driver.execute_script(js)

    def get_url(self, url):
        # 打开网址
        msg = '进入URL: %s' % url
        logger.info(msg)
        print(msg)
        self.driver.get(url)
        CaseInsertLogs.test_case_logs(self.task_obj.task_id, msg, 3)

    def sleep(self, sleep_seconds):
        """
        等待时间
        :param sleep_seconds: 单位秒
        :return:
        """
        msg = '休眠: %s秒' % sleep_seconds
        logger.info(msg)
        print(msg)
        time.sleep(int(sleep_seconds))
        CaseInsertLogs.test_case_logs(self.task_obj.task_id, msg, 3)

    def clear(self, by, locator):
        # 清空输入框
        msg = '清空输入框'
        logger.info(msg)
        print(msg)
        CaseInsertLogs.test_case_logs(self.task_obj.task_id, msg, 3)
        ObjectMap(self.driver, self.data).get_element(by, locator).clear()

    def input_value(self, by, locator, value):
        """
        输入框输入值
        :param by:
        :param locator:
        :param value:
        :return:
        """
        msg = '输入框输入: %s' % value
        logger.info(msg)
        print(msg)
        CaseInsertLogs.test_case_logs(self.task_obj.task_id, msg, 3)
        ObjectMap(self.driver, self.data).get_element(by, locator).send_keys(value)

    def clear_and_input(self, by, locator, value):
        """
        清除输入框再输入值
        :return:
        """
        msg = '清空输入框'
        logger.info(msg)
        print(msg)
        CaseInsertLogs.test_case_logs(self.task_obj.task_id, msg, 3)
        ObjectMap(self.driver, self.data).get_element(by, locator).clear()
        msg = '输入框输入: %s' % value
        logger.info(msg)
        print(msg)
        CaseInsertLogs.test_case_logs(self.task_obj.task_id, msg, 3)
        ObjectMap(self.driver, self.data).get_element(by, locator).send_keys(value)

    def upload_file(self, by, locator, value):
        """
        上传单个文件input标签  type="file"
        :param by:
        :param locator:
        :param value:
        :return:
        """
        ObjectMap(self.driver, self.data).get_element(by, locator).send_keys(value)
        msg = '上传文件: %s' % value
        logger.info(msg)
        print(msg)
        CaseInsertLogs.test_case_logs(self.task_obj.task_id, msg, 3)

    def upload_files(self, by, locator, value):
        """
        上传多个文件，value为文件夹路径，input标签
        :param by:
        :param locator:
        :param value:
        :return:
        """
        for root, dirs, files in os.walk(value):
            for i in files:
                ObjectMap(self.driver, self.data).get_element(by, locator).send_keys(value + '\\' + i)
                msg = '上传文件: %s' % i
                logger.info(msg)
                print(msg)
                CaseInsertLogs.test_case_logs(self.task_obj.task_id, msg, 3)

    def upload_file_windows(self, file_path):
        """
        :param file_path:上传文件的路径,需点击打开上传按钮，弹出windows窗口再调用 chrome 可调用
        :return:
        """
        dialog = win32gui.FindWindow("#32770", u"打开")  # 窗口左上角文字
        comboxex32 = win32gui.FindWindowEx(dialog, 0, "ComboBoxEx32", None)
        combox = win32gui.FindWindowEx(comboxex32, 0, "ComboBox", None)
        edit = win32gui.FindWindowEx(combox, 0, "Edit", None)
        button = win32gui.FindWindowEx(dialog, 0, "Button", "打开(&0)")
        win32gui.SendMessage(edit, win32con.WM_SETTEXT, None, file_path)
        win32gui.SendMessage(dialog, win32con.WM_COMMAND, 1, button)

    def assert_title(self, title_str):
        """
        断言页面标题
        :param title_str:
        :return:
        """
        msg = '断言: "%s"标题是否存在' % title_str
        logger.info(msg)
        CaseInsertLogs.test_case_logs(self.task_obj.task_id, msg, 3)
        assert title_str in self.driver.title, '%s标题不存在' % title_str
        print('"%s"标题存在' % title_str)

    def assert_string_in_page_source(self, ass_string):
        """
        断言字符串是否包含在源码中
        :param ass_string:
        :return:
        """
        msg = '断言: "%s"是否存在页面中' % ass_string
        logger.info(msg)
        CaseInsertLogs.test_case_logs(self.task_obj.task_id, msg, 3)
        assert ass_string in self.driver.page_source, "'%s'在页面中不存在" % ass_string
        print('"%s"存在页面中' % ass_string)

    def assert_equals(self, by, locator, value):
        """
        检查指定元素字符串与预期结果是否相同
        :return:
        """
        get_value = ObjectMap(self.driver, self.data).get_element(by, locator).get_attribute('value')
        get_text = ObjectMap(self.driver, self.data).get_element(by, locator).text
        if get_value == get_text:
            assert ObjectMap(self.driver, self.data).get_element(by, locator).get_attribute('value') == value
            msg = '%s=%s' % (ObjectMap(self.driver, self.data).get_element(by, locator).get_attribute('value'), value)
            logger.info(msg)
            # print(msg)
        elif get_value == '' or get_value is None:
            assert ObjectMap(self.driver, self.data).get_element(by, locator).text == value
            msg = '%s=%s' % (ObjectMap(self.driver, self.data).get_element(by, locator).text, value)
            logger.info(msg)
            # print(msg)
        elif get_text == '' or get_text is None:
            assert ObjectMap(self.driver, self.data).get_element(by, locator).get_attribute('value') == value
            msg = '%s=%s' % (ObjectMap(self.driver, self.data).get_element(by, locator).get_attribute('value'), value)
            logger.info(msg)
            # print(msg)
        else:
            assert ObjectMap(self.driver, self.data).get_element(by, locator).get_attribute('value') == value
            msg = '%s=%s' % (ObjectMap(self.driver, self.data).get_element(by, locator).get_attribute('value'), value)
            logger.info(msg)
            # print(msg)

    def assert_len(self, by, locator, value):
        """
        检查指定元素字符串长度
        :return:
        """
        get_value = ObjectMap(self.driver, self.data).get_element(by, locator).get_attribute('value')
        get_text = ObjectMap(self.driver, self.data).get_element(by, locator).text
        if get_value == get_text:
            assert len(
                ObjectMap(self.driver, self.data).get_element(by, locator).get_attribute('value')) == int(value)
            msg = '"%s"长度为: %s' % (ObjectMap(self.driver, self.data).get_element(by, locator).get_attribute('value'),value)
            logger.info(msg)
            # print(msg)
        elif get_value == '' or get_value is None:
            assert len(ObjectMap(self.driver, self.data).get_element(by, locator).text) == int(value)
            msg = '"%s"长度为: %s' % (ObjectMap(self.driver, self.data).get_element(by, locator).text, value)
            logger.info(msg)
            # print(msg)
        elif get_text == '' or get_text is None:
            assert len(
                ObjectMap(self.driver, self.data).get_element(by, locator).get_attribute('value')) == int(value)
            msg = '"%s"长度为: %s' % (ObjectMap(self.driver, self.data).get_element(by, locator).get_attribute('value'), value )
            logger.info(msg)
            # print(msg)
        else:
            assert len(
                ObjectMap(self.driver, self.data).get_element(by, locator).get_attribute('value')) == int(value)
            msg = '"%s"长度为: %s' % (ObjectMap(self.driver, self.data).get_element(by, locator).get_attribute('value'), value)
            logger.info(msg)
            # print(msg)

    def assert_element(self, by, locator):
        """
        判断元素是否存在
        :return:
        """
        assert ObjectMap(self.driver, self.data).get_element(by, locator)

    def assert_url(self, url):
        """
        判断当前网址是否和指定网址相同
        :param url:
        :return:
        """
        assert self.driver.current_url == url
        logger.info('%s==%s' % (self.driver.current_url, url))
        print('%s==%s' % (self.driver.current_url, url))

    def get_title(self):
        """
        获取页面标题
        :return:
        """
        try:
            msg = '获取页面标题：%s' % self.driver.title
            logger.info(msg)
            print(msg)
            CaseInsertLogs.test_case_logs(self.task_obj.task_id, msg, 3)
            return self.driver.title
        except Exception as e:
            msg = '获取页面标题失败: %s，原因：%s' % e, str(traceback.format_exc())
            logger.error(msg)
            print(msg)
            CaseInsertLogs.test_case_logs(self.task_obj.task_id, msg, 1)

    def get_page_source(self):
        """
        获取页面源码
        :return:
        """
        return self.driver.page_source

    def switch_to_frame(self, by, locator):
        """
        切换到frame页面内
        :param by:
        :param locator:
        :return:
        """
        self.driver.switch_to.frame(ObjectMap(self.driver, self.data).get_element(by, locator))

    def switch_to_default(self):
        """
        切换到默认的frame页面
        :return:
        """
        self.driver.switch_to.default_content()

    def switch_to_window(self, handle):
        """
        切换浏览器窗口
        :return:
        """
        msg = '当前窗口句柄', self.driver.current_window_handle
        print(msg)
        CaseInsertLogs.test_case_logs(self.task_obj.task_id, msg, 3)
        windows = self.driver.window_handles
        self.driver.switch_to.window(windows[int(handle)])

    def click(self, by, locator):
        """
        元素点击
        :return:
        """
        msg = '点击元素：%s' % locator
        logger.info(msg)
        print(msg)
        CaseInsertLogs.test_case_logs(self.task_obj.task_id, msg, 3)
        ObjectMap(self.driver, self.data).get_element(by, locator).click()

    def save_scree_shot(self, file=None, case_name=None):
        """
        屏幕截图
        :return:
        """
        picture_name = SCREENSHOTS_PATH
        if not os.path.exists(picture_name):
            os.makedirs(picture_name)
            picture_name = picture_name + '\\' + DirAndTime.get_current_time() + '.png'
        else:
            picture_name = picture_name + '\\' + DirAndTime.get_current_time() + '.png'
        try:
            self.driver.get_screenshot_as_file(picture_name)
            CaseInsertLogs.test_case_logs(self.task_obj.task_id, picture_name, 0)
            logger.info('开始自定义截图: %s' % picture_name)

        except Exception as e:
            msg = '保存截图失败: %s' % str(traceback.format_exc())
            logger.warning(msg, e)
            CaseInsertLogs.test_case_logs(self.task_obj.task_id, msg, 3)
        else:
            return picture_name

    def wait_find_element(self, by, locator):
        """
        显性等待30S判断单个元素是否可见，可见返回元素，否则抛出异常
        :param by: 传入参数为By.xx(xx为元素定位方式),Value(为元素定位内容)
        :param locator:
        :return:
        """
        if by.lower() in self.byDic:
            element = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((self.byDic[by.lower()], locator)))
            return element

    def not_wait_find_element(self, by, locator):
        """
        显性等待60S判断单个元素是否可见，可见返回元素，否则抛出异常
        :param by: 传入参数为By.xx(xx为元素定位方式),Value(为元素定位内容)
        :param locator:
        :return:
        """
        if by.lower() in self.byDic:
            element = WebDriverWait(self.driver, 60).until_not(
                EC.presence_of_element_located((self.byDic[by.lower()], locator)))
            return element

    def text_wait_find_element(self, by, locator):
        """
        显性等待30S判断单个元素是否可见，可见返回元素，否则抛出异常
        :param by: 传入参数为By.xx(xx为元素定位方式),Value(为元素定位内容)
        :param locator:
        :return:
        """
        if by.lower() in self.byDic:
            element = WebDriverWait(self.driver, 30).until(
                EC.text_to_be_present_in_element(self.byDic[by.lower()], locator))
            return element

    def not_text_wait_find_element(self, by, locator):
        """
        显性等待30S判断单个元素是否可见，可见返回元素，否则抛出异常
        :param by: 传入参数为By.xx(xx为元素定位方式),Value(为元素定位内容)
        :param locator:
        :return:
        """
        if by.lower() in self.byDic:
            element = WebDriverWait(self.driver, 30).until_not(
                EC.text_to_be_present_in_element(self.byDic[by.lower()], locator))
            return element

    def move_to_element(self, by, locator):
        """
        :param loc:loc = (By.xx,element)
        :param by:
        :param locator:
        :return:
        """
        element = self.driver.find_element(by, locator)
        t = self.driver.find_element(by, locator).text
        ActionChains(self.driver).move_to_element(element).perform()
        logger.info("鼠标悬浮在: %s" % t)
        print("鼠标悬浮在: %s" % t)

    def drop_down(self, p):
        """
        边框下拉滑动
        :param p:
        :return:
        """
        js = "var q=document.documentElement.scrollTop=%s" % p
        self.driver.execute_script(js)
        logger.info("滑动下拉框-距离: %s" % p)
        print("滑动下拉框-距离: %s" % p)

    def scroll_top(self):
        # 滚动到顶部
        js = "var q=document.documentElement.scrollTop=0"
        self.driver.execute_script(js)

    def scroll_end(self):
        # 滚动到底部
        js = "window.scrollTo(0,document.body.scrollHeight)"
        self.driver.execute_script(js)

    def enter(self, by, locator):
        # 模拟键盘回车
        ObjectMap(self.driver, self.data).get_element(by, locator).send_keys(Keys.ENTER)

    def down_end(self, count):
        """
        模拟按下键盘的下箭头方向键
        :params count 为按下的次数
        :return:
        """
        for i in range(count):
            self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            ActionChains(self.driver).key_down(Keys.DOWN).perform()