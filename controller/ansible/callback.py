#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
@Time: 2021/5/7 0007 下午 4:03
@Author: micheng. <safemonitor@outlook.com>
@File: callback.py
"""

import datetime
import json
import logging
import os
from collections import defaultdict

from ansible import constants as C
from ansible.plugins.callback import CallbackBase
from ansible.plugins.callback.default import CallbackModule
from ansible.plugins.callback.minimal import CallbackModule as CMDCallBackModule

from utils.time_utils import datetime2str_by_format
from controller.ansible.mongo_logs import Mongodb

logger = logging.getLogger('default')


class CallbackMixin:
    def __init__(self, display=None):
        # result_raw example: {
        #   "ok": {"hostname": {"task_name": {}，...},..},
        #   "failed": {"hostname": {"task_name": {}..}, ..},
        #   "unreachable: {"hostname": {"task_name": {}, ..}},
        #   "skipped": {"hostname": {"task_name": {}, ..}, ..},
        # }
        # results_summary example: {
        #   "contacted": {"hostname": {"task_name": {}}, "hostname": {}},
        #   "dark": {"hostname": {"task_name": {}, "task_name": {}},...,},
        #   "success": True
        # }
        self.results_raw = dict(
            ok=defaultdict(dict),
            failed=defaultdict(dict),
            unreachable=defaultdict(dict),
            skippe=defaultdict(dict),
        )
        self.results_summary = dict(
            contacted=defaultdict(dict),
            dark=defaultdict(dict),
            success=True
        )
        self.results = {
            'raw': self.results_raw,
            'summary': self.results_summary,
        }
        super().__init__()
        if display:
            self._display = display

        cols = os.environ.get("TERM_COLS", None)
        self._display.columns = 79
        if cols and cols.isdigit():
            self._display.columns = int(cols) - 1

    def display(self, msg):
        self._display.display(msg)

    def gather_result(self, t, result):
        self._clean_results(result._result, result._task.action)
        host = result._host.get_name()
        task_name = result.task_name
        task_result = result._result

        self.results_raw[t][host][task_name] = task_result
        self.clean_result(t, host, task_name, task_result)

    def close(self):
        if hasattr(self._display, 'close'):
            self._display.close()


class AdHocResultCallback(CallbackMixin, CallbackModule, CMDCallBackModule):
    """
    Task result Callback
    """

    def __init__(self, task_id, *args, **kwargs):
        super(AdHocResultCallback, self).__init__(*args, **kwargs)
        self.task_id = task_id

    context = None

    def clean_result(self, t, host, task_name, task_result):
        contacted = self.results_summary["contacted"]
        dark = self.results_summary["dark"]

        if task_result.get('rc') is not None:
            cmd = task_result.get('cmd')
            if isinstance(cmd, list):
                cmd = " ".join(cmd)
            else:
                cmd = str(cmd)
            detail = {
                'cmd': cmd,
                'stderr': task_result.get('stderr'),
                'stdout': task_result.get('stdout'),
                'rc': task_result.get('rc'),
                'delta': task_result.get('delta'),
                'msg': task_result.get('msg', '')
            }
        else:
            detail = {
                "changed": task_result.get('changed', False),
                "msg": task_result.get('msg', '')
            }

        if t in ("ok", "skipped"):
            contacted[host][task_name] = detail
        else:
            dark[host][task_name] = detail

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self.results_summary['success'] = False
        self.gather_result("failed", result)

        if result._task.action in C.MODULE_NO_JSON:
            CMDCallBackModule.v2_runner_on_failed(self,
                                                  result, ignore_errors=ignore_errors
                                                  )
        else:
            super().v2_runner_on_failed(
                result, ignore_errors=ignore_errors
            )

        now = datetime.datetime.now()
        time = datetime2str_by_format(now)
        results = {
            'task_id': self.task_id,
            'time': time,
            'hosts': [{
                'host': str(result._host.get_name()),
                'desc': '任务执行失败！',
                'task_result': result._result,
                'status': 'failed'
            }],
            'task_name': result.task_name
        }

        search_result = Mongodb().filter(task_id=self.task_id, status=None)
        if search_result:
            Mongodb().update({'task_id': self.task_id},
                             {'hosts': {'host': str(result._host.get_name()), 'desc': '任务执行失败', 'task_result': result._result, 'status': 'failed'}})
        else:
            Mongodb().insert(results)

    def v2_runner_on_ok(self, result):
        self.gather_result("ok", result)
        if result._task.action in C.MODULE_NO_JSON:
            CMDCallBackModule.v2_runner_on_ok(self, result)
        else:
            super().v2_runner_on_ok(result)

        now = datetime.datetime.now()
        time = datetime2str_by_format(now)
        results = {
            'task_id': self.task_id,
            'time': time,
            'hosts': [{
                'host': str(result._host.get_name()),
                'desc': '任务执行成功',
                'task_result': result._result,
                'status': 'ok'
            }],
            'task_name': result.task_name
        }

        search_result = Mongodb().filter(task_id=self.task_id, status=None)
        if search_result:
            Mongodb().update({'task_id': self.task_id},
                             {'hosts': {'host': str(result._host.get_name()), 'desc': '任务执行成功', 'task_result': result._result, 'status': 'ok'}})
        else:
            Mongodb().insert(results)

    def v2_runner_on_skipped(self, result):
        self.gather_result("skipped", result)
        super().v2_runner_on_skipped(result)

        now = datetime.datetime.now()
        time = datetime2str_by_format(now)
        results = {
            'task_id': self.task_id,
            'time': time,
            'hosts': [{
                'host': str(result._host.get_name()),
                'desc': '任务已跳过',
                'result': result._result,
                'status': 'skipped'
            }],
            'task_name': result.task_name
        }
        search_result = Mongodb().filter(task_id=self.task_id, status=None)
        if search_result:
            Mongodb().update({'task_id': self.task_id},
                             {'hosts': {'host': str(result._host.get_name()), 'desc': '任务已跳过', 'task_result': result._result, 'status': 'skipped'}})
        else:
            Mongodb().insert(results)

    def v2_runner_on_unreachable(self, result):
        self.results_summary['success'] = False
        self.gather_result("unreachable", result)
        super().v2_runner_on_unreachable(result)

        now = datetime.datetime.now()
        time = datetime2str_by_format(now)
        results = {
            'task_id': self.task_id,
            'time': time,
            'hosts': [{
                'host': str(result._host.get_name()),
                'desc': '主机不可到达',
                'result': result._result,
                'status': 'unreachable'
            }],
            'task_name': result.task_name
        }
        search_result = Mongodb().filter(task_id=self.task_id, status=None)
        if search_result:
            Mongodb().update({'task_id': self.task_id},
                             {'hosts': {'host': str(result._host.get_name()), 'desc': '主机不可到达', 'task_result': result._result, 'status': 'unreachable'}})
        else:
            Mongodb().insert(results)

    def v2_runner_on_start(self, *args, **kwargs):
        global task_name
        try:
            task_name = str(args[1]).split(':')[-1]
        except IndexError:
            pass
        now = datetime.datetime.now()
        time = datetime2str_by_format(now)
        results = {
            'task_id': self.task_id,
            'time': time,
            'hosts': [{
                'host': str(args[0]),
                'desc': '任务开始执行',
                'task_result': '',
                'status': 'started'
            }],
            'task_name': task_name
        }
        search_result = Mongodb().filter(task_id=self.task_id, status=None)
        if search_result:
            Mongodb().update({'task_id': self.task_id},
                             {'hosts': {'host': str(args[0]), 'desc': '任务开始执行', 'task_result': '', 'status': 'started'}})
        else:
            Mongodb().insert(results)

    def display_skipped_hosts(self):
        pass

    def display_ok_hosts(self):
        pass

    def display_failed_stderr(self):
        pass

    def set_play_context(self, context):
        # for k, v in context._attributes.items():
        #     print("{} ==> {}".format(k, v))
        if self.context and isinstance(self.context, dict):
            for k, v in self.context.items():
                setattr(context, k, v)


class CommandResultCallback(AdHocResultCallback):
    """
    Command result callback
    results_command: {
      "cmd": "",
      "stderr": "",
      "stdout": "",
      "rc": 0,
      "delta": 0:0:0.123
    }
    """
    def __init__(self, display=None, **kwargs):

        self.results_command = dict()
        super().__init__(display)

    def gather_result(self, t, res):
        super().gather_result(t, res)
        self.gather_cmd(t, res)

    def v2_playbook_on_play_start(self, play):
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        msg = '$ {} ({})'.format(play.name, now)
        self._play = play
        self._display.banner(msg)

    def v2_runner_on_unreachable(self, result):
        self.results_summary['success'] = False
        self.gather_result("unreachable", result)
        msg = result._result.get("msg")
        if not msg:
            msg = json.dumps(result._result, indent=4)
        self._display.display("%s | FAILED! => \n%s" % (
            result._host.get_name(),
            msg,
        ), color=C.COLOR_ERROR)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self.results_summary['success'] = False
        self.gather_result("failed", result)
        msg = result._result.get("msg", '')
        stderr = result._result.get("stderr")
        if stderr:
            msg += '\n' + stderr
        module_stdout = result._result.get("module_stdout")
        if module_stdout:
            msg += '\n' + module_stdout
        if not msg:
            msg = json.dumps(result._result, indent=4)
        self._display.display("%s | FAILED! => \n%s" % (
            result._host.get_name(),
            msg,
        ), color=C.COLOR_ERROR)

    def v2_playbook_on_stats(self, stats):
        pass

    def _print_task_banner(self, task):
        pass

    def gather_cmd(self, t, res):
        host = res._host.get_name()
        cmd = {}
        if t == "ok":
            cmd['cmd'] = res._result.get('cmd')
            cmd['stderr'] = res._result.get('stderr')
            cmd['stdout'] = res._result.get('stdout')
            cmd['rc'] = res._result.get('rc')
            cmd['delta'] = res._result.get('delta')
        else:
            cmd['err'] = "Error: {}".format(res)
        self.results_command[host] = cmd


class PlaybookResultCallBack(CallbackBase):
    """
    Custom callback model for handlering the output data of
    execute playbook file,
    Base on the build-in callback plugins of ansible which named `json`.
    """

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'Dict'

    def __init__(self, display=None, job_id=None):
        super(PlaybookResultCallBack, self).__init__(display)
        self.results = []
        self.output = ""
        self.item_results = {}  # {"host": []}
        self.job_id = job_id
        logger.info("PlayBook文件 回调函数, 任务Id: %s" % job_id)

    def _new_play(self, play):
        return {
            'play': {
                'name': play.name,
                'id': str(play._uuid)
            },
            'tasks': []
        }

    def _new_task(self, task):
        return {
            'task': {
                'name': task.get_name(),
            },
            'hosts': {}
        }

    def v2_playbook_on_no_hosts_matched(self):
        self.output = "skipping: No match hosts."
        logger.info(self.output)

    def v2_playbook_on_no_hosts_remaining(self):
        pass

    def v2_playbook_on_task_start(self, task, is_conditional):
        self.results[-1]['tasks'].append(self._new_task(task))

    def v2_playbook_on_play_start(self, play):
        self.results.append(self._new_play(play))

    def v2_playbook_on_stats(self, stats):
        hosts = sorted(stats.processed.keys())
        summary = {}
        for h in hosts:
            s = stats.summarize(h)
            summary[h] = s

        if self.output:
            pass
        else:
            self.output = {
                'plays': self.results,
                'stats': summary
            }

    def gather_result(self, res):
        if res._task.loop and "results" in res._result and res._host.name in self.item_results:
            res._result.update({"results": self.item_results[res._host.name]})
            del self.item_results[res._host.name]

        self.results[-1]['tasks'][-1]['hosts'][res._host.name] = res._result

    def v2_runner_on_ok(self, res, **kwargs):
        if "ansible_facts" in res._result:
            del res._result["ansible_facts"]

        self.gather_result(res)
        now = datetime.datetime.now()
        time = datetime2str_by_format(now)
        results = {
            'task_id': self.job_id,
            'time': time,
            'hosts': [{
                'host': str(res._host.get_name()),
                'desc': '任务执行成功',
                'task_result': res._result,
                'status': 'ok'
            }],
            'task_name': res.task_name
        }

        search_result = Mongodb().filter(task_id=self.job_id, status=None)
        if search_result:
            Mongodb().update({'task_id': self.job_id},
                             {'hosts': {'host': str(res._host.get_name()), 'desc': '任务执行成功', 'task_result': res._result, 'status': 'ok'}})
        else:
            Mongodb().insert(results)

    def v2_runner_on_failed(self, res, **kwargs):
        self.gather_result(res)
        now = datetime.datetime.now()
        time = datetime2str_by_format(now)
        results = {
            'task_id': self.job_id,
            'time': time,
            'hosts': [{
                'host': str(res._host.get_name()),
                'desc': '任务执行失败！',
                'task_result': res._result,
                'status': 'failed'
            }],
            'task_name': res.task_name
        }

        search_result = Mongodb().filter(task_id=self.job_id, status=None)
        if search_result:
            Mongodb().update({'task_id': self.job_id},
                             {'hosts': {'host': str(res._host.get_name()), 'desc': '任务执行失败', 'task_result': res._result, 'status': 'failed'}})
        else:
            Mongodb().insert(results)

    def v2_runner_on_unreachable(self, res, **kwargs):
        self.gather_result(res)
        now = datetime.datetime.now()
        time = datetime2str_by_format(now)
        results = {
            'task_id': self.job_id,
            'time': time,
            'hosts': [{
                'host': str(res._host.get_name()),
                'desc': '主机不可到达',
                'result': res._result,
                'status': 'unreachable'
            }],
            'task_name': res.task_name
        }
        search_result = Mongodb().filter(task_id=self.job_id, status=None)
        if search_result:
            Mongodb().update({'task_id': self.job_id},
                             {'hosts': {'host': str(res._host.get_name()), 'desc': '主机不可到达', 'task_result': res._result, 'status': 'unreachable'}})
        else:
            Mongodb().insert(results)

    def v2_runner_on_skipped(self, res, **kwargs):
        self.gather_result(res)
        now = datetime.datetime.now()
        time = datetime2str_by_format(now)
        results = {
            'task_id': self.job_id,
            'time': time,
            'hosts': [{
                'host': str(res._host.get_name()),
                'desc': '任务已跳过',
                'result': res._result,
                'status': 'skipped'
            }],
            'task_name': res.task_name
        }
        search_result = Mongodb().filter(task_id=self.job_id, status=None)
        if search_result:
            Mongodb().update({'task_id': self.job_id},
                             {'hosts': {'host': str(res._host.get_name()), 'desc': '任务已跳过', 'task_result': res._result, 'status': 'skipped'}})
        else:
            Mongodb().insert(results)

    def gather_item_result(self, res):
        self.item_results.setdefault(res._host.name, []).append(res._result)

    def v2_runner_item_on_ok(self, res):
        self.gather_item_result(res)

    def v2_runner_item_on_failed(self, res):
        self.gather_item_result(res)

    def v2_runner_item_on_skipped(self, res):
        self.gather_item_result(res)

