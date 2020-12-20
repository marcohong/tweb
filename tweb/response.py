from typing import Union, Any

from tweb.utils.ecodes import ECodes
__all__ = ['DATA_TYPE', 'content']

DATA_TYPE = Union[None, dict, list, tuple, str, bytes, float]


def content(code: int = ECodes.success[0],
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
