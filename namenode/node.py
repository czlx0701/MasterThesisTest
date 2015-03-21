from collections import defaultdict
from hash_ring import HashRing
import sys

from config import Config

class _NodeManager(object):
    __INSTANCE = None

    def __init__(self):
        super(_NodeManager, self).__init__()
        self.timestamp = 1
        self.locator = HashRing(Config.datanode)
        self.last_access = defaultdict(int)

    @classmethod
    def instance(cls):
        if not cls.__INSTANCE:
            cls.__INSTANCE = cls()
        return cls.__INSTANCE

    def get_key(self, filename, offset):
        import hashlib
        md5 = hashlib.md5()
        md5.update('%s!!%d' % (filename, offset))
        return md5.hexdigest()
     
    def get_servers(self, key):
        result = []
        for i in range(Config.copies):
            new_key = '%s!!%d' % (key, i)
            server = self.locator.get_node(new_key)
            result.append(server)
        return result

    def inc_timestamp(self):
        value = self.timestamp
        self.timestamp += 1
        return value

    def access_server(self, server):
        self.last_access[server] = self.inc_timestamp()

    def get_server(self, key):
        server = None
        timestamp = sys.maxint
        for node in self.get_servers(key):
            if self.last_access[node] < timestamp:
                timestamp = self.last_access[node]
                server = node
        self.access_server(server)
        return server

NodeManager = _NodeManager()
