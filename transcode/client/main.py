#!/usr/bin/env python
from common import init_base
init_base()

from datetime import timedelta
import logging
import os
from tornado import ioloop, gen

from basemessage import MessageRecv, MessageSend
from config import Config
from conn import ClientSession

class TaskDispatchRecv(MessageRecv):
    def parse(self):
        self.task = self.body['task']
        return True

    def send_finish(self):
        msg = SubtaskFinishSend(self.task['id'])
        self.reply(msg)

    def handle(self):
        ioloop.IOLoop.instance().add_timeout(
            timedelta(microseconds=100000), self.send_finish)

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
