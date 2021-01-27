#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : object_map.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2021/1/10
# @Desc  :
import traceback
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from utils.case_action.case_logs import CaseInsertLogs
from utils.case_action.config_read import ELEMENT_TIME
import logging
from auto_case.models import TestTask
logger = logging.getLogger('default')


class ObjectMap:
    def __init__(self, driver, data):
        self.driver = driver
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

    def get_element(self, by, locator):
        """
        查找单个元素对象
        :param by:
        :param locator:
        :return: 元素对象
        """
        try:
            if by.lower() in self.byDic:
                # element_time 元素定位超时时间
                element = WebDriverWait(self.driver, ELEMENT_TIME).until(
                    EC.presence_of_element_located((self.byDic[by.lower()], locator)))
                logger.info('通过: %s定位元素: %s' % (by, locator))
                return element
        except Exception as e:
            msg = '元素定位失败, 失败原因：%s' % str(traceback.format_exc())
            logger.error(msg, e)
            CaseInsertLogs.test_case_logs(self.task_obj.task_id, msg, 1)

    def get_elements(self, by, locator):
        """
        查找元素组
        :param by:
        :param locator:
        :return: 元素组对象
        """
        try:
            if by.lower() in self.byDic:
                # element_time 元素定位超时时间
                elements = WebDriverWait(self.driver, ELEMENT_TIME).until(
                    EC.presence_of_all_elements_located((by, locator)))
                logger.info('通过: %s定位元素组: %s' % (by, locator))
                return elements
        except Exception as e:
            msg = '元素组定位失败,失败原因：%s' % str(traceback.format_exc())
            logger.info(msg, e)
            CaseInsertLogs.test_case_logs(self.task_obj.task_id, msg, 1)