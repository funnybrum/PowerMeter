# Set of routines for managing low level system processes

import os
import subprocess
import time
from datetime import datetime

from lib import (
    config,
    log
)


def run_command(command, debug=False):
    """ Run command and return its output. """
    if debug:
        log('Executing command "%s"' % command)
    process = os.popen(command)
    output = process.read()
    process.close()
    if debug:
        log('Command result: %s' % output)
    return output


def run_background_command(command, line_count=50, timeout=10, debug=False):
    """ Run command and return its output. max_line specifies the maximum number of lines that should be read. """
    tmp_file = '%s/check_%s.tmp' % (config['tmp_folder'], os.getpid())
    output = ""
    start = datetime.now()
    try:
        subprocess.call('/usr/bin/nohup %s >%s 2>&1 &' % (command, tmp_file), shell=True)
        while (datetime.now() - start).total_seconds() < timeout:
            time.sleep(0.2)
            with open(tmp_file, 'r') as input:
                output = input.read()
            if output.count('\n') >= line_count:
                break
    except:
        pass
    finally:
        delete_file(tmp_file)
    return output


def delete_file(file_name):
    try:
        os.unlink(file_name)
    except:
        pass


def killall(name, debug=False):
    """ Kill all processes with the given name. Block till all of killed processes get stopped. """
    run_command('/usr/bin/killall -w %s 1>/dev/null 2>&1' % name, debug)


def kill(pid):
    """ kill the specified PID """
    run_command('/bin/kill %s' % pid)


def is_running(pid):
    """ Check if process with specified id is running. """
    return os.path.exists('/proc/%s' % pid)


def get_pid_process_name(pid):
    return run_command('ps -p %s -o comm=' % pid)


def check_background_process(pid, process_name):
    """
    Check if the specified PID is running and the process name matches the specified process name.
    :param pid: the pid
    :param process_name: the expected process name
    :return: True iff the process is running and it has the specified process name
    """
    return is_running(pid) and process_name == get_pid_process_name(pid)