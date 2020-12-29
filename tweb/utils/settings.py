import logging
from typing import Any
import tornado.web

# Default cookie secret, if server.conf not config
DEF_COOKIE_SECRET = 'w61oETXQAGaYLue6kL5gEmGeJJFsdDYh7EQnYsa3p7VseTP1o/Voyd='

DEF_TMP_DIR = '/tmp'

CORS_HEADERS = {
    'Access-Control-Allow-Credentials':
    'true',
    'Access-Control-Allow-Methods':
    'GET,POST,PUT,DELETE,OPTIONS',
    'Access-Control-Max-Age':
    '10000',
    'Access-Control-Allow-Headers': ('Accept, Authorization, '
                                     'Content-Length, Content-Type, '
                                     'Origin, X-Requested-With, '
                                     'X-Token, X-CSRFToken')
}


class TronadoStdout:
    '''
    See tornado.log define_logging_options method
    '''
    _data = dict(logging='info',
                 log_to_stderr=True,
                 log_file_prefix=None,
                 log_file_max_size=100 * 1000 * 1000,
                 log_file_num_backups=10,
                 log_rotate_when='midnight',
                 log_rotate_interval=1,
                 log_rotate_mode='size')

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        if key not in cls._data:
            raise KeyError
        cls._data[key] = value

    @classmethod
    def has_opt(cls, key: str) -> bool:
        return key not in cls._data

    @classmethod
    def get(cls, key: str) -> Any:
        return cls._data[key]

    @classmethod
    def getall(cls) -> dict:
        return cls._data


def default_log_func(handler: tornado.web.RequestHandler) -> None:
    if handler.get_status() < 400:
        log_method = logging.info
    elif handler.get_status() < 500:
        log_method = logging.warning
    else:
        log_method = logging.error
    req_time = 1000.0 * handler.request.request_time()
    log_method('%d %s %.2fms', handler.get_status(),
               handler._request_summary(), req_time)


def default_settings(debug: bool,
                     cookie_secret: str = DEF_COOKIE_SECRET) -> dict:
    data = {
        'access_control_allow_origin': '*',
        'cors': False,
        'cookie_domain': '',
        'cookie_expired': 12 * 60 * 60,
        'cookie_secret': cookie_secret,
        'debug': debug,
        'login_url': '/login',
        'xsrf_cookies': False
    }
    return data
