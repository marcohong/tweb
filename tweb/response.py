from typing import Union, Any

__all__ = ['DATA_TYPE', 'content', 'Codes']


# default codes, return json message code
class Codes:
    SUCCESS = 0
    FAILED = 1
    NO_LOGIN = 10001
    INVALID_TOKEN = 10002
    NO_PERMISSION = 10003


DATA_TYPE = Union[None, dict, list, tuple, str, bytes, float]


def content(code: int = Codes.SUCCESS,
            msg: str = None,
            data: DATA_TYPE = None,
            **kwargs: Any) -> dict:
    '''
    Respone json base contents.
    '''
    data = dict(code=code, msg=msg, data=data)
    if kwargs:
        data = {**data, **kwargs}
    return data
