#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright: (c) SmallFlyingPigs Organization. https://github.com/small-flying-pigs
# Copyright: (c) <pigs@dnsjia.com>
# Released under the AGPL-3.0 License.


"""
@Time: 2021/5/18 0026 上午 10:26
@Author: micheng. <safemonitor@outlook.com>
@File: runner.py
"""

import logging
import os
import shutil
from collections import namedtuple

from ansible import context
from ansible.playbook import Playbook
from ansible.module_utils.common.collections import ImmutableDict
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.vars.manager import VariableManager
from ansible.parsing.dataloader import DataLoader
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.playbook.play import Play
import ansible.constants as C

from controller.ansible.callback import AdHocResultCallback, PlaybookResultCallBack, CommandResultCallback
from exception.my_exception import AnsibleError
from controller.ansible.display import AdHocDisplay

__all__ = ["AdHocRunner", "PlayBookRunner", "CommandRunner"]
C.HOST_KEY_CHECKING = False
logger = logging.getLogger('default')

Options = namedtuple('Options', [
    'listtags', 'listtasks', 'listhosts', 'syntax', 'connection',
    'module_path', 'forks', 'remote_user', 'private_key_file', 'timeout',
    'ssh_common_args', 'ssh_extra_args', 'sftp_extra_args',
    'scp_extra_args', 'become', 'become_method', 'become_user',
    'verbosity', 'check', 'extra_vars', 'playbook_path', 'passwords',
    'diff', 'gathering', 'remote_tmp',
])


def get_default_options():
    options = dict(
        syntax=False,
        timeout=30,
        connection='ssh',
        forks=10,
        remote_user='root',
        private_key_file=None,
        become=None,
        become_method=None,
        become_user=None,
        verbosity=1,
        check=False,
        diff=False,
        gathering='implicit',
    )
    return options


class PlayBookRunner:
    """
    用于执行AnsiblePlaybook的接口.简化Playbook对象的使用.
    """

    # Default results callback
    results_callback_class = PlaybookResultCallBack
    loader_class = DataLoader
    variable_manager_class = VariableManager
    options = get_default_options()

    def __init__(self, inventory=None, options=None):
        """
        :param options: Ansible options like ansible.cfg
        :param inventory: Ansible inventory
        """
        if options:
            self.options = options
        C.RETRY_FILES_ENABLED = False
        self.inventory = inventory
        self.loader = self.loader_class()
        self.results_callback = self.results_callback_class()
        self.playbook_path = options.playbook_path
        self.variable_manager = self.variable_manager_class(
            loader=self.loader, inventory=self.inventory
        )
        self.passwords = options.passwords
        self.__check()

    def __check(self):
        if self.options.playbook_path is None or \
                not os.path.exists(self.options.playbook_path):
            raise AnsibleError(
                "Not Found the playbook file: {}.".format(self.options.playbook_path)
            )
        if not self.inventory.list_hosts('all'):
            raise AnsibleError('Inventory is empty')

    def get_result_callback(self, job_id=None):
        logger.info("PlayBookRunner get_result_callback任务ID是：%s" % str(job_id))
        return self.__class__.results_callback_class(display=AdHocDisplay(job_id),  job_id=job_id)

    def run(self, job_id):
        executor = PlaybookExecutor(
            playbooks=[self.playbook_path],
            inventory=self.inventory,
            variable_manager=self.variable_manager,
            loader=self.loader,
            passwords={"conn_pass": self.passwords}
        )

        context.CLIARGS = ImmutableDict(
            syntax=False,
            timeout=30,
            connection='ssh',
            forks=10,
            remote_user='root',
            private_key_file=None,
            become=None,
            become_method=None,
            become_user=None,
            verbosity=1,
            check=False,
            diff=False,
            gathering='implicit',
            remote_tmp='/tmp/.ansible',
            start_at_task = None
         )

        if executor._tqm:
            self.results_callback = self.get_result_callback(job_id)
            executor._tqm._stdout_callback = self.results_callback
        executor.run()
        executor._tqm.cleanup()
        logger.info("PlayBook执行完成")
        logger.info(self.results_callback.output)
        return self.results_callback.output


class AdHocRunner:
    """
    ADHoc Runner接口
    """
    results_callback_class = AdHocResultCallback
    results_callback = None
    loader_class = DataLoader
    variable_manager_class = VariableManager
    default_options = get_default_options()
    command_modules_choices = ('shell', 'raw', 'command', 'script', 'win_shell', 'copy')

    def __init__(self, inventory, options=None):
        self.options = self.update_options(options)
        self.inventory = inventory
        self.loader = DataLoader()
        self.variable_manager = VariableManager(
            loader=self.loader, inventory=self.inventory
        )

    def get_result_callback(self, execution_id=None):
        logger.info("get_result_callback任务ID是：%s" % str(execution_id))
        return self.__class__.results_callback_class(display=AdHocDisplay(execution_id),  task_id=execution_id)
        # return self.__class__.results_callback_class(display=AdHocDisplay(execution_id))

    @staticmethod
    def check_module_args(module_name, module_args=''):
        if module_name in C.MODULE_REQUIRE_ARGS and not module_args:
            err = "No argument passed to '%s' module." % module_name
            raise AnsibleError(err)

    def check_pattern(self, pattern):
        if not pattern:
            raise AnsibleError("Pattern `{}` is not valid!".format(pattern))
        if not self.inventory.list_hosts("all"):
            raise AnsibleError("Inventory is empty.")
        if not self.inventory.list_hosts(pattern):
            raise AnsibleError(
                "pattern: %s  dose not match any hosts." % pattern
            )

    def clean_args(self, module, args):
        if not args:
            return ''
        if module not in self.command_modules_choices:
            return args
        if isinstance(args, str):
            if args.startswith('executable='):
                _args = args.split(' ')
                executable, command = _args[0].split('=')[1], ' '.join(_args[1:])
                args = {'executable': executable, '_raw_params': command}
            else:
                args = {'_raw_params': args}
            return args
        else:
            return args

    def clean_tasks(self, tasks):
        cleaned_tasks = []
        for task in tasks:
            module = task['action']['module']
            args = task['action'].get('args')
            cleaned_args = self.clean_args(module, args)
            task['action']['args'] = cleaned_args
            self.check_module_args(module, cleaned_args)
            cleaned_tasks.append(task)
        return cleaned_tasks

    def update_options(self, options):
        _options = {k: v for k, v in self.default_options.items()}
        if options and isinstance(options, dict):
            _options.update(options)
        return _options

    def set_control_master_if_need(self, cleaned_tasks):
        modules = [task.get('action', {}).get('module') for task in cleaned_tasks]
        if {'ping', 'win_ping'} & set(modules):
            self.results_callback.context = {
                'ssh_args': '-C -o ControlMaster=no'
            }

    def run(self, tasks, pattern, play_name='Ansible Ad-hoc', gather_facts='no', execution_id=None):
        """
        :param tasks: [{'action': {'module': 'shell', 'args': 'ls'}, ...}, ]
        :param pattern: all, *, or others
        :param play_name: The play name
        :param gather_facts:
        :return:
        """
        self.check_pattern(pattern)
        self.results_callback = self.get_result_callback(execution_id)
        cleaned_tasks = self.clean_tasks(tasks)
        self.set_control_master_if_need(cleaned_tasks)
        context.CLIARGS = ImmutableDict(self.options)
        logger.info('cleaned_tasks--->>>>>>>', cleaned_tasks)
        play_source = dict(
            name=play_name,
            hosts=pattern,
            gather_facts=gather_facts,
            tasks=cleaned_tasks
        )

        play = Play().load(
            play_source,
            variable_manager=self.variable_manager,
            loader=self.loader,
        )
        loader = DataLoader()
        # used in start callback
        playbook = Playbook(loader)
        playbook._entries.append(play)
        playbook._file_name = '__adhoc_playbook__'
        tqm = TaskQueueManager(
            inventory=self.inventory,
            variable_manager=self.variable_manager,
            loader=self.loader,
            stdout_callback=self.results_callback,
            passwords={"conn_pass": self.options.get("password", "")}
        )
        try:
            tqm.send_callback('v2_playbook_on_start', playbook)
            tqm.run(play)
            tqm.send_callback('v2_playbook_on_stats', tqm._stats)
            # print("任务开始回调: ", self.results_callback)
            return self.results_callback
        except Exception as e:
            raise AnsibleError(e)
        finally:
            if tqm is not None:
                tqm.cleanup()
            shutil.rmtree(C.DEFAULT_LOCAL_TMP, True)

            self.results_callback.close()


class CommandRunner(AdHocRunner):
    results_callback_class = CommandResultCallback
    modules_choices = ('shell', 'raw', 'command', 'script', 'win_shell')

    def execute(self, cmd, pattern, module='shell'):
        if module and module not in self.modules_choices:
            raise AnsibleError("Module should in {}".format(self.modules_choices))

        tasks = [
            {"action": {"module": module, "args": cmd}}
        ]
        return self.run(tasks, pattern, play_name=cmd)
