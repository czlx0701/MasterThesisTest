#!/usr/bin/env python
from common import init_base
init_base()

import logging
import os
import tempfile
from tornado import ioloop, gen
from tornado.web import RequestHandler, Application, stream_request_body
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

from config import Config
from filemgr import FileManager
from node import NodeManager

@stream_request_body
class FileHandler(RequestHandler):
    def prepare(self):
        self.target_file = self.path_args[0]
        logging.info('Writing file %s...', self.target_file)
        if self.request.method == 'PUT':
            # (handle, filename) = tempfile.mkstemp()
            # os.unlink(filename)
            # self.tempfile = handle
            self.request.connection.set_max_body_size(5 * 1024 * 1024 * 1024)
            self.target_len  = int(self.request.headers['Content-Length'])
            self.current_pos = 0
            self.blocks = []
            self.now_data = b''
        elif self.request.method == 'HEAD':
            f_obj = FileManager.get_data(self.target_file)
            if f_obj:
                self.set_header('Content-Type', 'application/octet-stream')
                self.set_header('Content-Length', str(f_obj['size']))
            else:
                self.send_error(404)
            self.finish()
        else:
            self.send_error(405)
            self.finish()

    def remove_blocks(self):
        for block_url in self.blocks:
            logging.info('Removing %s', block_url)
            client = AsyncHTTPClient()
            request = HTTPRequest(url = block_url, method = 'DELETE')
            client.fetch(request)

    @gen.coroutine
    def data_received(self, data):
        self.now_data += data
        while len(self.now_data) >= Config.blocksize:
            block = self.now_data[:Config.blocksize]
            self.now_data = self.now_data[Config.blocksize:]
            yield self.write_block(block)

    def on_finish(self):
        # if self.tempfile:
        #     os.close(self.tempfile)
        logging.info("finish")
        if hasattr(self, 'now_data'):
            del self.now_data
        if hasattr(self, 'target_len'):
            if self.current_pos < self.target_len:
                logging.info('file length mismatch: %d, %d', self.current_pos, self.target_len)
                self.remove_blocks()
                FileManager.set_data(self.target_file, None)
            else:
                FileManager.set_data(
                        self.target_file,
                        {'size': self.target_len})
                logging.info("File stored.")

    def on_connection_close(self):
        if not self._finished:
            self.on_finish()

    @gen.coroutine
    def write_block(self, block):
        key = NodeManager.get_key(self.target_file, self.current_pos)
        servers = NodeManager.get_servers(key)
        requests = []
        for server in servers:
            client = AsyncHTTPClient()
            NodeManager.access_server(server)
            block_url = 'http://%s/block/%s' % (server, key)
            self.blocks.append(block_url)
            request = HTTPRequest(url = block_url,
                    request_timeout = 600,
                    method = 'PUT', body = block)
            requests.append(client.fetch(request))
        logging.info('Writing block at %d (len = %d) to servers: %s',
                self.current_pos, len(block), ' '.join(servers))
        if not self._finished:
            self.write('Writing block at %d (len = %d) to servers: %s\n' %
                    (self.current_pos, len(block), ' '.join(servers)))
        self.current_pos += len(block)
        self.flush()
        yield requests

    def put(self, filename):
        if len(self.now_data):
            self.write_block(self.now_data)
        self.write('OK!')
        self.finish()

class BlockHandler(RequestHandler):
    def get(self, filename, offset):
        offset = int(offset)
        key = NodeManager.get_key(filename, offset)
        target_url = 'http://%s/block/%s' % (NodeManager.get_server(key), key)
        self.redirect(target_url)

def main():
    application = Application([
        (r'/file/([^\/]+)', FileHandler),
        (r'/file/([^\/]+)/([0-9]+)', BlockHandler)
    ])
    application.listen(8888)
    ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
    main()
