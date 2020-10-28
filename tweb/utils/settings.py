import logging
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
