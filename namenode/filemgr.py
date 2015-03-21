from datetime import datetime
import json
import logging
import os
import struct

from config import Config

class _FileManager(object):
    __INSTANCE  = None
    __DATA_FILE = 'fileinfo.dat'
    def __init__(self):
        super(_FileManager, self).__init__()
        self.files = {}
        self.last_update = datetime.min
        self.ensure_data()

    @classmethod
    def instance(cls):
        if not cls.__INSTANCE:
            cls.__INSTANCE = cls()
        return cls.__INSTANCE

    def set_data(self, name, value):
        if not value:
            if name in self.files:
                del self.files[name]
            else:
                return
        else:
            self.files[name] = value
        self.flush()

    def get_data(self, name):
        self.ensure_data()
        return self.files.get(name)

    def ensure_data(self):
        if not os.path.exists(self.__DATA_FILE):
            return
        last_modify = os.path.getmtime(self.__DATA_FILE)
        last_modify = datetime.fromtimestamp(last_modify)
        if last_modify > self.last_update:
            logging.info('Reload file info')
            self.files.clear()
            with open(self.__DATA_FILE, 'rb') as f:
                data = f.read()
            while len(data):
                item_len = struct.unpack('i', data[:4])[0]
                item_val = data[4: 4 + item_len]
                data = data[4 + item_len:]
                item = json.loads(item_val)
                self.files[item['name']] = item['value']

    def flush(self):
        data = []
        for name in self.files:
            item = json.dumps({
                'name':  name,
                'value': self.files[name]
            })
            item = struct.pack('i', len(item)) + item
            data.append(item)
        data = b''.join(data)
        logging.info('Store file info')
        with open(self.__DATA_FILE, 'wb') as f:
            f.write(data)
        self.last_update = datetime.now()

FileManager = _FileManager.instance()
