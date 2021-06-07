#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
# @File  : tree.py
# @Author: 风哥
# @Email: gujiwork@outlook.com
# @Date  : 2020/12/1
# @Desc  :
"""


def tree_filter(serializer_data, filter_name=None):
    """
    树型化
    """
    tree_dict = {}
    tree_data = []
    try:
        for item in serializer_data:
            tree_dict[item['id']] = item
        for i in tree_dict:
            if filter_name:
                if i not in filter_name:
                    continue
            if tree_dict[i]['pid']:
                pid = tree_dict[i]['pid']
                parent = tree_dict[pid]
                parent.setdefault('children', []).append(tree_dict[i])
            else:
                tree_data.append(tree_dict[i])
        results = tree_data
    except KeyError:
        results = serializer_data
    return results
