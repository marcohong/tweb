import threading
from typing import Any


class SingleClass:
    '''
    Not support init method with args/kwargs
    '''
    _instance_lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any):
        if not hasattr(cls, '_instance'):
            with cls._instance_lock:
                if not hasattr(cls, '_instance'):
                    cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance
