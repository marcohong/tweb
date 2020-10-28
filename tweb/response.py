import io
from typing import Union, Any
from enum import Enum

__all__ = [
    'DATA_TYPE', 'RespType', 'content', 'success', 'failure', 'jsonify',
    'string', 'files', 'stream', 'render_html'
]


# return json message code
class State(Enum):
    SUCCESS = 0
    FAILED = 1
    NO_LOGIN = 10001
    INVALID_TOKEN = 10002
    NO_PERMISSION = 10003


class RespType(Enum):
    text = 'text'
    json = 'json'
    files = 'files'
    stream = 'stream'
    template = 'template'


DATA_TYPE = Union[None, dict, list, tuple, str, bytes, float]


def content(state: int = State.SUCCESS.value,
            msg: str = None,
            data: DATA_TYPE = None,
            **kwargs: Any) -> dict:
    '''
    Respone json base contents.
    '''
    data = dict(state=state, msg=msg, data=data)
    if kwargs:
        data = {**data, **kwargs}
    return {'__resp_type__': RespType.json, 'data': data}


def success(msg: str = None, data: DATA_TYPE = None, **kwargs: Any) -> dict:
    '''
    Return success message.
    '''
    return content(State.SUCCESS.value, msg=msg, data=data, **kwargs)


def failure(msg: str = None, data: DATA_TYPE = None, **kwargs: Any) -> dict:
    '''
    Return failure message.
    '''
    return content(State.FAILED.value, msg=msg, data=data, **kwargs)


def jsonify(**kwargs: Any) -> dict:
    '''
    Back custom data format json.
    '''
    return {'__resp_type__': RespType.json, 'data': kwargs}


def string(text: str) -> dict:
    '''
    Response str to browser
    '''
    return {'__resp_type__': RespType.text, 'data': text}


def render_html(template_name: str, **kwargs: Any) -> dict:
    '''
    tornado render html
    '''
    kwargs.update({'template_name': template_name})
    return {'__resp_type__': RespType.template, 'data': kwargs}


def files(filename: str, stream: io.BytesIO) -> dict:
    '''
    Download file.

    usage::

        stream = io.BytesIO()
        stream.write('test'.encode('utf8'))
        #or
        stream = io.BytesIO('test'.encode('utf8'))

    :param filename: `<str>` file name
    :param stream: `<BytesIO>` stream object
    '''
    return {
        '__resp_type__': RespType.files,
        'data': {
            'stream': stream,
            'filename': filename
        }
    }


def stream(stream: io.BytesIO, content_type: str) -> dict:
    '''
    Output file, e.g: qrcode

    :param stream: `<BytesIO>` stream object
    :param content_type: `<str>` e.g: image/jpg
    :return:
    '''
    return {
        '__resp_type__': RespType.stream,
        'data': {
            'stream': stream,
            'content-type': content_type
        }
    }
