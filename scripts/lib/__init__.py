from __future__ import absolute_import

import inspect
import os
import sys

from datetime import datetime
from lib.yaml_config import load_config


config = {}

if os.getenv('APP_CONFIG'):
    config = load_config(os.getenv('APP_CONFIG'))


def log(message):
    """ Log message to stdout with time prefix. """

    frame = inspect.stack()[1]
    filename = frame[0].f_code.co_filename
    filename = os.path.basename(filename).replace('.py', '')

    timestamp = datetime.now().strftime('[%d/%m/%y %H:%M:%S]')
    print('[%s] %s %s' % (filename, timestamp, message))
    sys.stdout.flush()
