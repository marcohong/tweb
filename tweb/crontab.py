'''
Task factory.

usage::

    class TestFactory(TaskFactory):
        def __init__(self):
            super().__init__()
            self.log_file = 'test.log'

        async def job(args):
            # if max_worker, use self.semaphore:
            async with self.semaphore
                do...

        async def execute(self):
            tasks = [self.job(x) for x in range(10)]
            await asyncio.wait(tasks)

    if __name__ == "__main__":
        Test().start(daemon=True, pid='test.pid', _fork=True)
'''
import os
import sys
import traceback
import logging
import asyncio
import uvloop
from typing import Callable, Awaitable, Optional

from tweb.config import Config
from tweb.utils.strings import get_real_path
from tweb.utils.daemon import fork
from tweb.utils.signal import SignalHandler
from tweb.exceptions import trace_info
from tweb.utils.settings import DEF_TMP_DIR


def get_log_path(opt, log_file):

    assert log_file, 'Log file name can not be empty'
    path = Config().get_option('log', opt, DEF_TMP_DIR)
    log_path = get_real_path(os.path.join(path, log_file))
    if not os.path.exists(os.path.dirname(log_path)):
        try:
            os.makedirs(os.path.dirname(log_path))
        except OSError:
            logging.error(trace_info())
            sys.exit(1)
    return log_path


class TaskFactory:
    def __init__(self):
        self._loop = None
        self.max_worker: int = 4
        self.semaphore: asyncio.Semaphore = None
        self.delay: int = 1
        self._run_flag_: int = 1
        self.log_file: str = 'task.log'
        self.log_dir: str = ''
        self.log_dir_opt: str = 'crontab_base_log_dir'
        # Record start task and finish task log flag.
        self._log_active: bool = True

    def _init_logging(self) -> None:
        _format = ('[%(levelname)s %(asctime)s %(process)d %(module)s:'
                   '%(lineno)d]: %(message)s')
        if self.log_dir:
            os.makedirs(self.log_dir)
            log_path = os.path.join(self.log_dir, self.log_file)
        else:
            log_path = get_log_path(self.log_dir_opt, self.log_file)
        logging.basicConfig(filename=log_path,
                            level=logging.INFO,
                            datefmt='%Y-%m-%d %H:%M:%S',
                            format=_format)

    async def prepare(self):
        pass

    def datas_split(self, datas: list, size: int) -> Optional[list]:
        if not datas or (not size or size < 0):
            return datas
        total = len(datas)
        return [datas[i:i + size] for i in range(0, total, size)]

    def _stop_handler(self, signalnum, frame):
        logging.error(f'Received system input signal: {signalnum}')
        self._run_flag_ = 0

    def start(self,
              daemon: bool = False,
              pid: str = None,
              _fork: bool = True) -> None:
        '''Start job.

        :param daemon: `<bool>` false: executed once after exit
            true: background process
        :param pid: `<str>` pid file, default log_file name
        :param _fork: `<bool>` fork child process if true
        :return:
        '''
        SignalHandler.listen(self._stop_handler)
        if _fork:
            pid = pid if pid else f'{self.log_file}.pid'
            if os.path.exists(DEF_TMP_DIR):
                pid = os.path.join(DEF_TMP_DIR, pid)
            fork(pid)
        try:
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
            self._loop = asyncio.get_event_loop()
            self._loop.run_until_complete(self._start(daemon))
        except KeyboardInterrupt:
            logging.error('Manually paused[KeyboardInterrupt error]')
        finally:
            if self._log_active:
                logging.info('Task done.')

    async def _start(self, daemon: bool = False) -> Callable[..., Awaitable]:
        self._init_logging()
        info = (f'Task started, daemon: {daemon}, pid: {os.getpid()}, '
                f'max worker: {self.max_worker}, delay: {self.delay}.')
        if self._log_active:
            logging.info(info)
        print(info)
        await self.prepare()
        if self.max_worker:
            self.semaphore = asyncio.Semaphore(self.max_worker)
        while self._run_flag_:
            try:
                await self.execute()
                await self.commit()
            except Exception:
                logging.error(''.join(
                    traceback.format_exception(*sys.exc_info())))
                await self.rollback()
                await self.close()
            if not daemon:
                break
            await asyncio.sleep(self.delay)

    async def execute(self) -> Callable[..., Awaitable]:
        '''
        do something...
        '''
        pass

    async def close(self):
        pass

    async def rollback(self):
        pass

    async def commit(self):
        pass
