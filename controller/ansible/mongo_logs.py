#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
@Time: 2021/5/18 0007 下午 10:26
@Author: micheng. <safemonitor@outlook.com>
@File: mongo_logs.py
"""

import pymongo
from decouple import config


class Mongodb(object):
    """
    Mongo CURD
    """

    def __init__(self, db='ansible', collection='task_log'):
        self.client = pymongo.MongoClient(host=config('MONGO_HOST'), port=int(config('MONGO_PORT')))
        self.db = self.client[db]
        self.col = self.db[collection]

    def insert(self, content):
        return self.col.insert_one(content)

    # def find_all(self, content=None): result = [] for i in self.col.find({"status.host": "i-bp10rydhf43t7r07v8we",
    # "task_id": "14270011787911182284566604763026587502"}): result.append(i) return result

    def filter(self, task_id, status):
        result = []
        if task_id and status:
            agg = [{"$match": {"task_id": str(task_id)}}, {"$unwind": "$hosts"}, {
                "$match": {"hosts.status": status}}, {
                      "$group": {"_id": "$_id", "task_id": {"$first": "$task_id"}, "hosts": {"$push": "$hosts"}}}]

            job_result = self.col.aggregate(agg)
            for res in job_result:
                del res['_id']
                result.append(res)
            return result

        elif task_id and status == '' or status is None:
            job_result = self.col.find({'task_id': str(task_id)}, {"_id": 0}).sort([('time', 1)])
            for res in job_result:
                result.append(res)
            return result
        else:
            return False

    def update(self, search_value: dict, update_value: dict) -> dict:
        ret = self.col.update(search_value, {"$addToSet": update_value})
        # self.col.update({"status.host": "i-bp10rydhf43t7r07v8we","task_id":
        # "14270011787911182284566604763026587502"}, {"$push": {'11': 22}})
        return ret
