#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : wait_unit.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2021/1/10
# @Desc  :

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from utils.case_action.config_read import ELEMENT_TIME


class WaitUnit(object):
    # 元素等待时间, ELEMENT_TIME 默认30s
    def __init__(self, driver):
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
        self.driver = driver
        self.wait = WebDriverWait(self.driver, ELEMENT_TIME)

    def presence_of_element_located(self, by, locator):
        """
        显示等待一个元素出现在DOM树中，不存在则抛出异常，存在则返回对象
        :param by:
        :param locator:
        :return: 元素对象
        """
        try:
            if by.lower() in self.byDic:
                self.wait.until(EC.presence_of_element_located((self.byDic[by.lower()], locator)))
            else:
                raise TypeError('未找到元素，请检查定位方式')
        except Exception as e:
            raise e

