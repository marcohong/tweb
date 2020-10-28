import functools
from typing import Callable, Any

from .exceptions import Error, FormError
from .response import failure, RespType
from tweb.utils.escape import json_dumps
from tweb.utils.log import logger


def callback(func: Callable[..., Any]) -> Callable[..., Any]:
    '''
    Async callback decorator.

    usage::

    class TestHandler(BaseHandler):

        @callback
        def get(self):
            return success(data='test')
            # if used self.render_html('index.html', data='')
            # return success(data='test', url='index.html')
    '''
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        self = args[0]

        def _wrapper(result):
            '''Callback response result.'''
            if self._finished:
                return

            if not result or not isinstance(result, dict):
                _write_error(self)
                return

            resp_type = result.get('__resp_type__', None)
            if resp_type == RespType.json:
                self.set_json_header()
                _write_data(self, json_dumps(result['data']))
            elif resp_type == RespType.template:
                self.render_html(**result['data'])
            elif resp_type == RespType.stream:
                self.set_header('Content-Type', result['content-type'])
                _write_data(self, result['stream'].getvalue())
            elif resp_type == RespType.files:
                _write_file(self, result['data'])
            elif resp_type == RespType.text:
                _write_data(self, result['data'])
            else:
                _write_error(self, **result)

        try:
            _result = await func(*args, **kwargs)
        except Error as err:
            _result = _process_error(self, err)
        _wrapper(_result)

    return wrapper


def _write_data(self, data: str) -> None:
    self.finish(data)


def _write_error(self, code: int = 400, **kwargs: Any) -> None:
    self.set_status(400)
    self.write_error(400, **kwargs)


def _process_error(self, err) -> dict:
    if isinstance(err, FormError):
        return failure(self.lang(err.message), errors=err.errors)
    logger.error(err.message)
    return failure(msg=self.lang(err.message))


def _write_file(self, result: dict) -> None:
    '''
    Write stream to browser
    '''
    self.set_stream_header(result['filename'])
    stream = result['stream']
    stream.seek(0, 0)
    while 1:
        data = stream.read(4096)
        if not data:
            break
        self.write(data)
    stream.close()
    self.finish()
