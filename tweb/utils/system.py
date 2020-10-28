import os
import logging
from tweb.exceptions import trace_info


def create_file(path):
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except OSError:
            logging.error(trace_info)
            return False
        else:
            return True
    elif os.access(path, os.W_OK):
        return True
    else:
        return False
