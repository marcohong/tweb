import os
import logging
from logging.handlers import TimedRotatingFileHandler
from typing import Callable, Optional

from tweb.config import Config
from tweb.utils.strings import get_real_path
from tweb.utils.system import create_file

__all__ = ['LOG', 'logger']


class Logger:
    _format = ('[%(levelname)s  %(asctime)s %(process)d %(module)s:'
               '%(lineno)d] %(message)s')

    @staticmethod
    def get_log_path(conf, option: str) -> Optional[str]:
        '''
        Get log path.

        :param conf: `<tweb.config>`
        :param option: `<str>` config option
        :param default: `<str>` default log file path
        :return:
        '''
        path = conf.get_option('log', option, default='')
        if not path:
            return None
        log_path = get_real_path(path)
        base_dir = os.path.dirname(log_path)
        flag = create_file(base_dir)
        if not flag:
            logging.warning(
                f"Create log directory '{base_dir}' fail, use '/tmp' directory"
            )
            log_path = f'/tmp/{os.path.basename(log_path)}'
        return log_path

    @classmethod
    def create_logger(
            cls,
            when: str = 'W6',
            interval: int = 1,
            backup_count: int = 0,
            formatter: logging.Formatter = None) -> Callable[..., None]:
        '''
        Create logger.

        :param when: `<str>` split log routes, see tornado log format
        :param interval: `<int>` see tornado log format
        :param backup_count: `<int>` see tornado log format
        :param formatter: `<logging.Formatter>` default None
        :return:
        '''
        conf = Config()
        # if not conf:
        #     return logging.getLogger(__name__)
        level = logging.getLevelName(
            conf.get_option('log', 'level', 'INFO').upper())
        logger = logging.getLogger('root')
        logger.setLevel(level)
        archive = conf.get_bool_option('log', 'archive', True)
        if archive:
            if not formatter:
                formatter = logging.Formatter(cls._format,
                                              datefmt='%Y-%m-%d %H:%M:%S')
            log_path = cls.get_log_path(conf, 'access_path')
            if not log_path:
                return logger
            file_hander = TimedRotatingFileHandler(log_path,
                                                   when=when,
                                                   interval=interval,
                                                   backupCount=backup_count)
            file_hander.setFormatter(formatter)
            file_hander.setLevel((level))
            logger.addHandler(file_hander)
            # handler = logging.FileHandler(log_path)
            # handler.setLevel(level)
            # handler.setFormatter(formatter)
            # logger.addHandler(handler)
        logger.is_archive = archive
        return logger


LOG = Logger.create_logger()
logger = LOG
