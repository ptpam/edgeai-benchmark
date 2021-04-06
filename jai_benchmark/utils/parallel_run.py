# Copyright (c) 2018-2021, Texas Instruments
# All Rights Reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys
import multiprocessing
import collections
import time
from .progress_step import *


class ParallelRun:
    def __init__(self, num_processes, desc='tasks', blocking=True, maxinterval=10.0):
        self.desc = desc
        self.num_processes = num_processes
        self.queued_tasks = collections.deque()
        self.maxinterval = maxinterval
        self.blocking = blocking

    def enqueue(self, task):
        self.queued_tasks.append(task)

    def run(self):
        assert len(self.queued_tasks) > 0, f'at least one task must be queued, got {len(self.queued_tasks)}'
        self.start_time = time.time()
        return self._run_parallel()

    def _run_sequential(self):
        result_list = []
        for task_id, task in progress_step(self.queued_tasks, desc='tasks'):
            result = task()
            result_list.append(result)
        #
        return result_list

    def _run_parallel(self):
        # create process pool and queue the tasks - 'spawn' may be more stable than the default 'fork'
        process_pool = multiprocessing.get_context('spawn').Pool(self.num_processes)
        results_iterator = process_pool.imap_unordered(self._worker, self.queued_tasks)
        if self.blocking:
            # run a loop to monitor the progress
            result_list = self._run_monitor(results_iterator)
            return result_list
        else:
            return results_iterator
        #

    def _run_monitor(self, results_iterator):
        results_list = []
        num_completed = num_completed_prev = 0
        num_tasks = len(self.queued_tasks)
        pbar_tasks = progress_step(iterable=range(num_tasks), desc=self.desc, position=1)
        while num_completed < num_tasks:
            # check if a result is available
            try:
                result = results_iterator.__next__(timeout=self.maxinterval)
                results_list.append(result)
                num_completed = len(results_list)
            except multiprocessing.TimeoutError as e:
                pass
            #
            pbar_tasks.update(num_completed-num_completed_prev)
            num_completed_prev = num_completed
        #
        pbar_tasks.close()
        print('\n')
        return results_list

    def _worker(self, task):
        return task()