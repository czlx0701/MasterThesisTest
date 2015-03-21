import json
import logging
import sys

class _Config(object):
    __INSTANCE = None
    __FILE_NAME = 'config.json'

    def __init__(self):
        super(_Config, self).__init__()
        try:
            with open(self.__FILE_NAME, 'rb') as f:
                self.__data = json.loads(f.read())
        except Exception:
            logging.exception("Failed to read config file.")
            sys.exit(1)

    @classmethod
    def instance(cls):
        if not cls.__INSTANCE:
            cls.__INSTANCE = cls()
        return cls.__INSTANCE

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        return self.__data[name]

Config = _Config.instance()
