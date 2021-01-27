#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : pagination.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2020/12/1
# @Desc  :
from rest_framework.pagination import PageNumberPagination


class MyPageNumberPagination(PageNumberPagination):
    page_size = 10
    page_query_param = 'page'
    page_size_query_param = 'page_size'
    max_page_size = 40


class MenuPagination(PageNumberPagination):
    page_size = 100
    page_query_param = 'page'
    page_size_query_param = 'page_size'
    max_page_size = 100


class MaxPagination(PageNumberPagination):
    page_size = 1000
    page_query_param = 'page'
    page_size_query_param = 'page_size'
    max_page_size = 1000
