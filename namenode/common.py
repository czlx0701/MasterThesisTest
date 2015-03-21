import logging
import os
import sys

def get_base_dir():
    return os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

def add_lib_path(path = None):
    libpath = os.path.join(get_base_dir(), 'libs')
    if not path is None:
        libpath = os.path.join(libpath, path)
    if not libpath in sys.path:
        sys.path.append(libpath)

def init_base():
    logging.basicConfig(
            level = logging.INFO)
    add_lib_path()
