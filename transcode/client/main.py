#!/usr/bin/env python
from common import init_base
init_base()

import logging
import os
import tempfile
from tornado import ioloop
from tornado.process import Subprocess

from basemessage import MessageRecv, MessageSend
from config import Config
from conn import ClientSession

class TaskDispatchRecv(MessageRecv):
    def parse(self):
        self.task = self.body['task']
        return True

    def send_finish(self, ret_code):
        msg = SubtaskFinishSend(self.task['id'])
        self.reply(msg)
        if ret_code:
            logging.error('failed to finish the transcode task: %s', self.task)
        self.__cleanup()

    def __create_output(self):
        (handle, filename) = tempfile.mkstemp()
        os.close(handle)
        self.outputs.append(filename)
        return filename

    def __cleanup(self):
        for name in self.outputs:
            os.unlink(name)

    def __build_cmdline(self):
        task = self.task
        cmdline = [
            Config.conv_exe,
            Config.conv_args['start'],  str(task['start']),
            Config.conv_args['length'], str(task['length']),
            Config.conv_args['input'],  task['filename']
        ]
        for config in task['configs']:
            cmdline.extend(config)
            cmdline.extend([
                Config.conv_args['output'], self.__create_output()
            ])
        return cmdline

    def handle(self):
        self.outputs = []
        cmdline = self.__build_cmdline()
        process = Subprocess(cmdline, stdin = Subprocess.STREAM)
        process.stdin.close()
        process.set_exit_callback(self.send_finish)

    @classmethod
    def get_type(cls):
        return 'task_dispatch'

class AvailableSend(MessageSend):
    def __init__(self):
        super(AvailableSend, self).__init__(type_str='available')

class SubtaskFinishSend(MessageSend):
    def __init__(self, subtask_id):
        super(SubtaskFinishSend, self).__init__(type_str='subtask-finish')
        self.body['subtask_id'] = subtask_id

def send_available(session):
    session.send(AvailableSend())

def main():
    from basemessage import HandShakeRecv
    for msgcls in (HandShakeRecv, TaskDispatchRecv):
        msgcls.register()
    ClientSession(Config.server_host, Config.server_port, Config.name, send_available)
    ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
