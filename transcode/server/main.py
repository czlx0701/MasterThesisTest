#!/usr/bin/env python
from common import init_base
init_base()

from datetime import datetime
import json
import logging
from Queue import Queue
import uuid

from tornado import ioloop, gen
from tornado.process import Subprocess
from tornado.web import RequestHandler, Application

from basemessage import MessageRecv, MessageSend
from config import Config
from conn import Server

class TaskDispatchSend(MessageSend):
    def __init__(self, task):
        super(TaskDispatchSend, self).__init__(type_str='task_dispatch')
        self.body['task'] = task

class Manager(object):
    __INSTANCE = None
    def __init__(self):
        super(Manager, self).__init__()
        self.available_session = Queue()
        self.task_queue    = Queue()
        self.subtask_queue = Queue()
        self.pending_task  = {}
        self.finished_task = {}
        self.running_task  = {}
        self.subtask       = {}
        self.creating_task = False

    def __check_tasks(self):
        while not self.available_session.empty():
            if self.subtask_queue.empty():
                self.__generate_subtask()
                return
            if self.subtask_queue.empty():
                break
            session = self.available_session.get()
            sub_id  = self.subtask_queue.get()
            subtask = self.subtask[sub_id]
            msg     = TaskDispatchSend(subtask)
            session.send(msg)
            task = self.running_task[subtask['task_id']]
            if not 'start_time' in task:
                task['start_time'] = datetime.now()
        if self.subtask_queue.empty():
            self.__generate_subtask()

    def __add_subtask(self, start, length, task):
        subtask = {
            'id':       uuid.uuid4().hex,
            'task_id':  task['id'],
            'filename': task['task']['filename'],
            'configs':  Config.conv_config,
            'start':    start,
            'length':   length
        }
        sub_id = subtask['id']
        self.subtask_queue.put(sub_id)
        self.subtask[sub_id] = subtask
        task['blocks'] += 1
        task['subtasks'].add(subtask['id'])

    # def __create_subtask(self, duration, time_unit, task):
    #     task = dict(task)
    #     task_id = task['id']
    #     del task['id']
    #     task_item = {
    #         'id':       task_id,
    #         'task':     task,
    #         'subtasks': set(),
    #         'blocks':   0,
    #     }
    #     self.running_task[task_item['id']] = task_item
    #     start = 0
    #     length = min(duration, time_unit)
    #     while start < duration - 1e-5:
    #         length = min(duration - start, duration / 10)
    #         self.__add_subtask(start, length, task_item)
    #         start += length

    def __create_subtask(self, duration, time_unit, task):
        task = dict(task)
        task_id = task['id']
        del task['id']
        task_item = {
            'id':       task_id,
            'task':     task,
            'subtasks': set(),
            'blocks':   0,
        }
        self.running_task[task_item['id']] = task_item
        start = 0
        length = min(duration, time_unit)
        self.__add_subtask(start, length, task_item)
        start += length
        while start < duration - 1e-5:
            length = min(duration - start, time_unit * 2)
            self.__add_subtask(start, length, task_item)
            start += length

    # def __create_subtask(self, duration, time_unit, task):
    #     task = dict(task)
    #     task_id = task['id']
    #     del task['id']
    #     task_item = {
    #         'id':       task_id,
    #         'task':     task,
    #         'subtasks': set(),
    #         'blocks':   0,
    #     }
    #     self.running_task[task_item['id']] = task_item
    #     start = 0
    #     self.__add_subtask(start, duration, task_item)

    def __parse_probe(self, out, err, task):
        try:
            data = json.loads(out.decode('iso8859-1'))
            data = data['format']
            bitrate = float(data['bit_rate']) / 8
            duration = float(data['duration'])
            size = int(float(data['size']))
            if duration < 1:
                duration = size / bitrate
            time_unit = Config.blocksize / bitrate / Config.copies / Config.parallel
            self.__create_subtask(duration, time_unit, task)
        except Exception:
            logging.exception('failed to probe %s.\n stdout:\n%s\nstderr:\n%s',
                    task, out, err)

    @gen.coroutine
    def __generate_subtask(self):
        if self.creating_task or self.task_queue.empty():
            return
        self.creating_task = True
        task_id = self.task_queue.get()
        task    = self.pending_task[task_id]
        del self.pending_task[task_id]
        cmdline = list(Config.probe_args)
        cmdline.insert(0, Config.probe_exe)
        cmdline.append(task['filename'])
        process = Subprocess(cmdline, stdin = Subprocess.STREAM,
                stdout = Subprocess.STREAM,
                stderr = Subprocess.STREAM)
        process.stdin.close()
        out, err = yield [process.stdout.read_until_close(), process.stderr.read_until_close()]
        self.__parse_probe(out, err, task)
        self.creating_task = False
        self.__check_tasks()

    def add_task(self, task):
        task_id = task['id']
        self.pending_task[task_id] = task
        self.task_queue.put(task_id)
        if self.subtask_queue.empty():
            self.__generate_subtask()

    def finish_subtask(self, subtask_id, session):
        if not subtask_id in self.subtask:
            logging.warn('subtask %s not found, ignore.')
        else:
            subtask = self.subtask[subtask_id]
            del self.subtask[subtask_id]
            task_id = subtask['task_id']
            task = self.running_task[task_id]
            if subtask_id in task['subtasks']:
                task['subtasks'].remove(subtask_id)
                if not len(task['subtasks']):
                    del self.running_task[task_id]
                    self.finished_task[task_id] = {
                        'id':   task_id,
                        'task': task['task'],
                        'time_used': (datetime.now() - task['start_time']).total_seconds()
                    }
                    logging.info('task finished: %s', self.finished_task[task_id])
            else:
                logging.warn('subtask %s already finished.')
        self.session_available(session)

    def query_task(self, task_id):
        if task_id in self.running_task:
            task = dict(self.running_task[task_id])
            if 'start_time' in task:
                task['start_time'] = str(task['start_time'])
            task['progress'] = 100 - len(task['subtasks']) * 100.0 / task['blocks']
            task['status'] = 'running'
            del task['subtasks']
        elif task_id in self.finished_task:
            task = dict(self.finished_task[task_id])
            task['progress'] = 100.0
            task['status'] = 'finished'
        elif task_id in self.pending_task:
            task = dict(self.pending_task[task_id])
            task['progress'] = 0.0
            task['status'] = 'waiting'
        else:
            return {
                'type': 'error',
                'msg':  'task not found'
            }
        task['type'] = 'task_info'
        return task

    def session_available(self, session):
        logging.info('session %s available', session.name)
        self.available_session.put(session)
        self.__check_tasks()

    @classmethod
    def instance(cls):
        if not cls.__INSTANCE:
            cls.__INSTANCE = cls()
        return cls.__INSTANCE

class AvailableRecv(MessageRecv):
    def handle(self):
        Manager.instance().session_available(self.session)

    @classmethod
    def get_type(cls):
        return 'available'

class SubtaskFinishRecv(MessageRecv):
    def parse(self):
        self.subtask_id = self.body['subtask_id']
        return True

    def handle(self):
        Manager.instance().finish_subtask(self.subtask_id, self.session)

    @classmethod
    def get_type(cls):
        return 'subtask-finish'

class TaskHandler(RequestHandler):
    def put(self, filename):
        filename = 'hdfs://%s/file/%s' % (Config.namenode, filename)
        task = {
            'id':       uuid.uuid4().hex,
            'filename': filename
        }
        Manager.instance().add_task(task)
        self.write(task)

    def get(self, task_id):
        self.write(Manager.instance().query_task(task_id))

def main():
    from basemessage import HandShakeRecv
    for msgcls in (HandShakeRecv, AvailableRecv, SubtaskFinishRecv):
        msgcls.register()
    application = Application([
        (r'/task/([^\/]+)', TaskHandler)
    ])
    application.listen(Config.api_port)
    Server().listen(Config.server_port)
    ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
