import json
import logging

from tornado.ioloop import IOLoop

class MessageRecv(object):
    __MAPPING = {}
    def __init__(self, data, type_str, session):
        super(MessageRecv, self).__init__()
        self.body = data
        self.type_str = type_str
        self.session = session

    def parse(self):
        return True

    def handle(self):
        pass

    def reply(self, msg):
        self.session.send(msg)

    @classmethod
    def get_type(cls):
        raise NotImplementedError()

    @classmethod
    def register(cls):
        cls.__MAPPING[cls.get_type()] = cls

    @classmethod
    def deregister(cls):
        del cls.__MAPPING[cls.get_type()]

    @classmethod
    def parse_message(cls, raw, session):
        data = json.loads(raw)
        type_str = data['__type']
        del data['__type']
        ctor = cls.__MAPPING.get(type_str)
        if not ctor:
            logging.warn('unknown message %s: %s', type_str, data)
            return
        try:
            msg = ctor(data, type_str, session)
            if msg.parse():
                logging.info('got %s message from session %s: %s',
                        type_str, session.name, data)
                IOLoop.current().add_callback(msg.handle)
            else:
                logging.warn('failed to parse message %s: %s', type_str, data)
        except Exception:
            logging.exception('parse message %s: %s', type_str, data)

class MessageSend(object):
    def __init__(self, type_str):
        super(MessageSend, self).__init__()
        self.type_str = type_str
        self.body = {}

    def serialize(self):
        data = dict(self.body)
        data['__type'] = self.type_str
        return json.dumps(data)

class HandShakeSend(MessageSend):
    def __init__(self, local_name):
        super(HandShakeSend, self).__init__(type_str = 'handshake')
        self.body['name'] = local_name

class HandShakeRecv(MessageRecv):
    def parse(self):
        self.name = self.body['name']
        return True

    def handle(self):
        self.session.set_name(self.name)

    @classmethod
    def get_type(cls):
        return 'handshake'

