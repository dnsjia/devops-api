#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
@Author: 风哥
@Mail: gujiwork@outlook.com
@File:selenium_config.py
@Time:2020/10/24 16:52
"""
from django.conf import settings
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
from decouple import config
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent



class SeleniumInit():

    @classmethod
    def create_windows(self, url):
        chrome_options = Options()
        chrome_options.add_argument('--disable-gpu')
        driver_path = os.path.join(BASE_DIR, config('DRIVER_PATH'))
        driver = webdriver.Chrome(executable_path=driver_path, chrome_options=chrome_options)
        driver.get(url=url)
        return driver