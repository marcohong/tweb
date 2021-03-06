import os
import sys
import platform
import logging


def fork(pid_file: str) -> None:
    if platform.system() not in ('Linux', 'Darwin'):
        logging.error('Does not support window platforms.')
        sys.exit(1)
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as err:
        logging.error(f'fork #1 failed: {err.errno} ({err.strerror})')
        sys.exit(1)
    # create new session, sub process to become the first process
    os.setsid()
    # modify the working directory
    os.umask(0)
    try:
        pid = os.fork()
        if pid > 0:
            write_pid(pid_file, pid)
            sys.exit(0)
    except OSError as err:
        logging.error(f'fork #2 failed: {err.errno} ({err.strerror})')
        sys.exit(1)


def write_pid(pid_file: str, pid: int) -> None:
    with open(pid_file, 'w') as f:
        f.write(str(pid))
