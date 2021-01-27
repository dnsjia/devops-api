#!/bin/env python3
# -*- coding: utf-8 -*-

"""
@Time: 2020/9/27 17:45
@Author: yu.jiang <safemonitor@outlook.com>
@License: Apache License
@File: rest_page.py

"""
import six
from django.core.paginator import InvalidPage
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """"

    /api/v1/xxx/getList?page=1&pageSize=10
    """

    # 默认每页显示的数据条数
    page_size = 10
    # 页数
    page_query_param = 'page'
    # URL传入的每页显示条数
    page_size_query_param = 'pageSize'
    # 每页显示数据最大条数
    max_page_size = 50

    # 根据ID从大到小排列
    ordering = "id"

    def paginate_queryset(self, queryset, request, view=None):
        """
        Paginate a queryset if required, either returning a
        page object, or `None` if pagination is not configured for this view.
        """
        page_size = self.get_page_size(request)
        if not page_size:
            return None

        paginator = self.django_paginator_class(queryset, page_size)
        page_number = request.query_params.get(self.page_query_param, 1)
        if page_number in self.last_page_strings:
            page_number = paginator.num_pages

        try:
            self.page = paginator.page(page_number)
        except InvalidPage as exc:
            msg = self.invalid_page_message.format(
                page_number=page_number, message=str(exc)
            )
            print('Page Not Found')
            paginator = self.django_paginator_class(queryset, page_size)
            page_number = 1
            self.page = paginator.page(page_number)
            print(self.page, 'Self-Page-------------------')

           # raise NotFound(msg)

        if paginator.num_pages > 1 and self.template is not None:
            # The browsable API should display pagination controls.
            self.display_page_controls = True

        self.request = request
        return list(self.page)
