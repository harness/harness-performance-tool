#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2015 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from locust import HttpUser, task, SequentialTaskSet, events
import sys
from utilities import utils
from ci_view_execution import CI_VIEW_EXECUTION
from ci_create_pipeline import CI_CREATE_PIPELINE
from ci_update_pipeline import CI_UPDATE_PIPELINE
from ci_execute_pipeline import CI_EXECUTE_PIPELINE
from ci_pipeline_run import CI_PIPELINE_RUN
from ci_pipeline_remote_run import CI_PIPELINE_REMOTE_RUN
from entities import ORGANIZATION, PROJECT, PIPELINE
from ci_pipeline_remote_save import CI_PIPELINE_REMOTE_SAVE
from ci_pipeline_save import CI_PIPELINE_SAVE
from trigger_pipeline import TRIGGER_PIPELINE
from cd_pipeline_run import CD_PIPELINE_RUN
from ci_pipeline_webhook_run import CI_PIPELINE_WEBHOOK_RUN

USER_CREDENTIALS = None
custom_module_random_selection = False
current_task_index = 0
global_task_set = []

@events.init_command_line_parser.add_listener
def _(parser):
    parser.add_argument("--test-scenario", type=str, default="CI_CREATE_PIPELINE", help="")
    parser.add_argument("--pipeline-url", type=str, default="", help="optional")
    parser.add_argument("--pipeline-execution-count", type=int, default=0, help="optional")
    parser.add_argument("--env", type=str, include_in_web_ui=False, default="on-prem", help="eg: on-prem")

class CUSTOM_CLASS(HttpUser):
    def on_start(self):
        tasks_set = []
        classes = self.environment.parsed_options.test_scenario

        # Script Loading
        try:
            classes_arr = utils.getCustomInputAsList(classes)
            for x in classes_arr:
                tasks_set.append(getattr(sys.modules[__name__], x.strip()))
            print("TASK SET EXECUTING : " + str(tasks_set))
        except Exception:
            print(
                'Custom Script is not imported in the tasks.py file or Its not created in the Locust GitHub Repo')

        if len(tasks_set) == 1:
            print("single module execution")
            self.__class__.tasks = tasks_set
        elif custom_module_random_selection == True:
            print("multi module execution with random selection")
            self.__class__.tasks = tasks_set
        else:
            print("multi module execution with serial selection")
            global global_task_set
            global_task_set = tasks_set
            self.__class__.tasks = [TaskSequence]

class TaskSequence(SequentialTaskSet):
    def get_next_task(self):
        global global_task_set
        global current_task_index

        task = global_task_set[current_task_index]
        current_task_index = (current_task_index + 1) % len(global_task_set)
        return task

    @task
    def task_sequence(self):
        next_task = self.get_next_task()
        next_task()