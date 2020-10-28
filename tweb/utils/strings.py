import os
import sys
import uuid
import time
import string
import random
import datetime


def get_root_path(path: str = None) -> str:
    '''
    Get project base path, default start shell dir

    :param path: `<str>`
    :return:
    '''
    if path and not os.path.exists(path):
        path = os.path.dirname(os.path.abspath(sys.argv[0]))
    else:
        path = os.path.dirname(os.path.abspath(sys.argv[0]))
    return path


ROOT_PATH = get_root_path()


def get_real_path(path: str, root_path: str = ROOT_PATH) -> str:
    '''
    get file real path
    '''
    if path in ['.', '..'] or path.startswith('../'):
        return os.path.realpath(path)
    elif path.startswith('~/'):
        user_home = os.path.expanduser('~')
        return path.replace('~', user_home)
    elif path.startswith('/'):
        return path
    else:
        return os.path.join(root_path, path)


def browser(user_agent: str, origin_agent: str) -> str:
    if 'chrome' in user_agent:
        return 'Chrome'
    elif 'firefox' in user_agent:
        return 'Firefox'
    elif 'safari' in user_agent:
        return 'Safari'
    browser = origin_agent.split()[-1]
    if '/' in browser:
        return browser.split('/')[0]
    return browser


def get_browser(user_agent: str) -> str:
    '''
    get browser name
    '''
    origin_agent = user_agent
    user_agent = user_agent.lower()
    if not user_agent:
        return 'UnKnown'
    elif 'windows' in user_agent:
        if 'trident' in user_agent:
            return 'IE'
        elif 'edge' in user_agent:
            return 'Edge'
    elif 'mac os x' in user_agent:
        return browser(user_agent, origin_agent)
    elif 'android' in user_agent:
        return browser(user_agent, origin_agent)
    return browser(user_agent, origin_agent)


def get_os(user_agent: str) -> str:
    '''
    get user system type
    '''
    user_agent = user_agent.lower()
    if 'windows' in user_agent:
        return 'Windows'
    elif 'ipad' in user_agent:
        return 'iPad'
    elif 'iphone' in user_agent:
        return 'iPhone'
    elif 'mac os x' in user_agent:
        return 'Mac OS X'
    elif 'android' in user_agent:
        return 'Android'
    elif 'linux' in user_agent:
        return 'Linux'
    else:
        return 'UnKnown'


def is_chinese(word: str) -> bool:
    if isinstance(word, bytes):
        word = str(word)
    for ch in word:
        if '\u4e00' <= ch <= '\u9fa5':
            return True
    return False


def req_is_json(request) -> bool:
    '''
    Check request is json.

    :param request: `<tornado.web.httputil.HTTPServerRequest>`
    :return: `<bool>` True is json, else return False
    '''
    if 'application/json' in request.headers.get('Accept', ''):
        return True
    return False


def get_file_name() -> str:
    '''
    :return: uuid name
    '''
    return uuid.uuid4().hex


def get_date(fmt: str = '%Y-%m-%d', days: int = 0) -> str:
    date = datetime.datetime.now()
    if days:
        date = date + datetime.timedelta(days=days)
    return date.strftime(fmt)


def get_now_date(fmt: str = '%Y-%m-%d') -> str:
    '''return date str'''
    return datetime.datetime.now().strftime(fmt)


def get_now_time(fmt: bool = True) -> datetime.datetime:
    if fmt:
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return datetime.datetime.now()


def datetime_to_str(date: datetime.datetime,
                    fmt: str = '%Y-%m-%d %H:%M:%S') -> str:
    return date.strftime(fmt)


def str_to_datetime(str_time: str) -> datetime.datetime:
    if ' ' not in str_time and len(str_time) < 11:
        str_time = f'{str_time} 00:00:00'
    return datetime.datetime.strptime(str_time, '%Y-%m-%d %H:%M:%S')


def get_timestamp(millisecond: bool = False):
    if millisecond:
        return int(time.time() * 1000)
    return int(time.time())


def timestamp_to_time(timestamp: float) -> str:
    '''
    conevrt timestamp to datetime yyyy-mm-dd HH24:MM:SS
    '''
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))


def get_rand_digit(length) -> str:
    if length > 1:
        start = int('1' + '0'.zfill(length - 1))
        ended = int(f'{start}0') - 1
    else:
        start, ended = 0, 9
    digit = random.randint(start, ended)
    return f'{digit}'


def get_rand_str(length: int = 8) -> str:
    '''
    :param length: max value 62
    random string from (A-Za-z0-9)
    :param length: string length
    '''
    length = length if length <= 62 else 62
    return ''.join(random.sample(string.ascii_letters + string.digits, length))


def get_uuid(to_hex: bool = False) -> str:
    if to_hex:
        return uuid.uuid4().hex
    return str(uuid.uuid4())
