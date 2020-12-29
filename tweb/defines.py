import sys
from typing import Callable, Any
from argparse import ArgumentParser, Namespace

from tweb.utils.single import SingleClass

_conf_files = frozenset(['server', 'local', 'dev'])


class CommandLine(SingleClass):
    parser = None
    _args = None

    def __init__(self) -> None:
        if not self.parser:
            self.parser = ArgumentParser()
            self.initialize()

    def initialize(self) -> None:
        assert self.parser
        self.parser.add_argument('-c',
                                 '--conf',
                                 type=str,
                                 default='server',
                                 choices=['server', 'local', 'dev'],
                                 help='Read configure for options')
        self.parser.add_argument('-p',
                                 '--port',
                                 type=int,
                                 default=0,
                                 help='Run on the given port')
        self.parser.add_argument('-pid',
                                 type=str,
                                 default=None,
                                 help='pid file path')
        self.parser.add_argument('-proc',
                                 type=int,
                                 default=None,
                                 help='Process number, default none')
        self.parser.add_argument('-d',
                                 '--daemon',
                                 action='store_true',
                                 help='background process')
        self.parser.add_argument('-debug',
                                 action='store_true',
                                 help='Enable debug mode')
        self.parser.add_argument('-s',
                                 '--signal',
                                 type=str,
                                 choices=['restart', 'stop'],
                                 help='Restart or stop server')

    def parse_args(self) -> Namespace:
        self._args = self.parser.parse_args()
        return self._args

    @property
    def args(self) -> Namespace:
        if not self._args:
            self.parse_args()
        return self._args

    @property
    def define(self) -> ArgumentParser:
        return self.parser

    @property
    def add_argument(self) -> Callable[..., Any]:
        return self.parser.add_argument

    @classmethod
    def parse_conf(cls) -> str:
        args = sys.argv
        name = None
        for idx, opt in enumerate(args[1:]):
            if not opt.startswith('--conf') and not opt.startswith('-c'):
                continue
            if '=' in opt:
                name = opt.split('=')[1]
            elif len(args) > idx + 2:
                name = args[idx + 2]
            else:
                name = 'server'
            break
        if name not in _conf_files:
            name = 'server'
        return name
