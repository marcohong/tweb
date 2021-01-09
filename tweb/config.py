import os
import logging
import configparser
import string
import random
from typing import Optional

from tweb.utils.environment import env
from tweb.utils.single import SingleClass
from tweb.defines import CommandLine

__all__ = ['conf', 'Config']

config_template = '''
[setting]
port = {port}
processes = 1
language = zh_CN
cors = True
access_control_allow_origin = *
cookie_domain =
cookie_secret_name = X-Token
cookie_secret = {cookie_secret}
_debug = False
_enable_jwt = True

[log]
level = INFO
archive = True
crontab_base_log_dir = /tmp
access_path = /tmp/access.log

[database]
# mysql://user:passwd@ip:port/my_db
# mysql+pool://user:passwd@ip:port/my_db?charset=utf8&max_connections=50&stale_timeout=20
# postgresql://user:passwd@ip:port/my_db?connect_timeout=60&max_connections=50&stale_timeout=30
# postgresql+pool://user:passwd@ip:port/my_db?connect_timeout=60&max_connections=50&stale_timeout=30

[redis]
# redis://:password@host:6379/0?encoding=utf-8
# unix: /path/to/redis.sock
center_redis_url = redis://localhost:6379/0?encoding=utf8
'''


def get_cmd_conf() -> Optional[str]:
    '''
    Get conf path from command lines.

    usage::

    python3 main.py -c server
    python3 main.py --conf server
    python3 main.py --conf=server
    '''
    name = CommandLine.parse_conf()
    return get_conf_file(name)


def get_conf_file(name: str, port: int = 8888) -> Optional[str]:
    _path = os.path.join(env.getenv('ROOT_PATH'), 'conf', f'{name}.conf')
    if not os.path.exists(_path):
        if not os.path.exists(os.path.dirname(_path)):
            if not env.getenv('CREATE_CONFIG'):
                return None
            os.makedirs(os.path.dirname(_path))
        cookie_secret = ''.join(
            random.sample(string.ascii_letters + string.digits + '=/$@&', 64))
        with open(_path, 'w') as file_:
            text = config_template.format(port=port,
                                          cookie_secret=cookie_secret)
            file_.write(text.strip())
    return _path


class Config(SingleClass):
    conf: configparser.ConfigParser = None
    conf_path: str = None

    def initialize(self, path: str = None) -> None:
        '''
        if path and path exists, return
        '''
        if path:
            if not os.path.exists(path):
                return None
        else:
            if self.conf:
                return self
            path = get_cmd_conf()
            if not path or not os.path.exists(path):
                return None
        self.conf_path = path
        self.parser(self.conf_path)
        return self

    def parser(self, path: str = None) -> None:
        if not path or not env.getenv('ROOT_PATH'):
            raise ValueError('path and env ROOT_PATH value is none.')
        _path = path or env.getenv('ROOT_PATH')
        self.conf = configparser.ConfigParser()
        self.conf.read(_path)

    def get_option(self,
                   section: str,
                   option: str,
                   default: str = None,
                   ignore: bool = True) -> str:
        '''
        Get config.conf option
        :param section: `<str>`
        :param option: `<str>`
        :param default: default value
        :param ignore: ignore error output
        :return: option value or default value
        '''
        try:
            val = self.conf.get(section, option)
            return val if val else default
        except configparser.Error as err:
            if not ignore:
                logging.warning(err.message)
            return default

    def get_bool_option(self,
                        section: str,
                        option: str,
                        default: bool = False,
                        ignore: bool = True) -> bool:
        '''
        Return boolean result.
        '''
        result = self.get_option(section, option, default=None, ignore=ignore)
        if not result:
            return default
        if result.lower() in ('false', '0'):
            return False
        return True

    def get_int_option(self,
                       section: str,
                       option: str,
                       default: int = None,
                       ignore: bool = True) -> int:
        '''
        Return int result or None(if not found and default=None).
        '''
        result = self.get_option(section, option, default=None, ignore=ignore)
        if not result:
            return default
        return int(result) if result.isdigit() else default

    def set_option(self, section: str, option: str, value: str) -> None:
        '''
        Update config.conf value
        '''
        try:
            if not self.conf.has_section(section):
                self.conf.add_section(section)
            self.conf.set(section, option, value)
            self.conf.write(open(self.conf_path, 'w'))
        except configparser.Error as err:
            logging.error(err.message)
            raise ValueError(err.message)

    def get_process_num(self) -> int:
        '''Return process number'''
        return self.get_int_option('setting', 'processes', 1)

    def get_language(self) -> str:
        '''Return config.conf default language, default en_US'''
        return self.get_option('setting', 'language', 'en_US')


conf = Config()
conf.initialize()
