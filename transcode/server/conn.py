import logging
import struct
from Queue import Queue

from tornado import gen
from tornado.ioloop import IOLoop
from tornado.iostream import StreamClosedError
from tornado.tcpserver import TCPServer
from tornado.tcpclient import TCPClient

from basemessage import MessageRecv, HandShakeSend

class Session(object):
    def __init__(self, stream, address):
        self.name = 'unnamed'
        self.stream = stream
        self.address = address
        self.__queue = Queue()
        self.__writing = False

    def set_name(self, name):
        self.name = name

    def bind_handler(self):
        self.stream.set_nodelay(True)
        self.stream.read_bytes(4, callback=self.__handle_read)
        self.__check_write()

    @gen.coroutine
    def __handle_read(self, len_str):
        data = None
        try:
            while True:
                data_len = struct.unpack('i', len_str)[0]
                data = yield self.stream.read_bytes(data_len)
                try:
                    MessageRecv.parse_message(data, self)
                except StreamClosedError:
                    raise
                except Exception:
                    logging.exception('parse_message: %s', data)
                len_str = yield self.stream.read_bytes(4)
        except StreamClosedError:
            logging.info('connection %s closed.', self.address)
        except Exception:
            logging.exception('handle_read: %s, close connectioni %s', data, self.address)
            self.stream.close()

    def send(self, msg):
        self.__queue.put(msg.serialize())
        self.__check_write()

    def __check_write(self):
        if not self.__writing:
            self.__do_write()

    @gen.coroutine
    def __do_write(self):
        if not self.stream:
            return
        self.__writing = True
        while not self.__queue.empty():
            data = self.__queue.get()
            data = struct.pack('i', len(data)) + data
            logging.info('send %s', data)
            yield self.stream.write(data)
        self.__writing = False

    def close(self):
        self.stream.close()

class ClientSession(Session):
    def __init__(self, host, port, local_name, handler):
        super(ClientSession, self).__init__(None, None)
        self.host = host
        self.port = port
        self.local_name = local_name
        self.handler = handler
        self.__create_connection()

    @gen.coroutine
    def __create_connection(self):
        client = TCPClient()
        self.stream = yield client.connect(self.host, self.port)
        self.address = 'local'
        self.bind_handler()
        self.send(HandShakeSend(self.local_name))
        IOLoop.current().add_callback(self.handler, session = self)

class Server(TCPServer):
    def handle_stream(self, stream, address):
        logging.info('accept connection from %s', address)
        Session(stream, address).bind_handler()

