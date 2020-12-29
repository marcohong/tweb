import os
import sys
import socket
import asyncio
import types
from functools import partial
import signal as signal
from typing import Any, Union
try:
    import uvloop
    uvloop.install()
except ImportError:
    uvloop = None

import tornado.web
from tornado.ioloop import IOLoop
import tornado.options
from tornado.log import enable_pretty_logging

from .defines import CommandLine
from .router import app, Router
from tweb.utils import daemon
from tweb.utils.attr_util import AttrDict
from tweb.utils.signal import SignalHandler
from tweb.utils import strings
from tweb.utils.environment import env
from tweb.utils.settings import default_settings, TronadoStdout,\
    DEF_COOKIE_SECRET


class Application(tornado.web.Application):
    def __init__(self,
                 handlers=None,
                 default_host=None,
                 transforms=None,
                 **settings):
        super().__init__(handlers=handlers,
                         default_host=default_host,
                         transforms=transforms,
                         **settings)

    def init_with_loop(self,
                       loop: asyncio.BaseEventLoop,
                       tasks: list = None) -> None:
        if tasks and isinstance(tasks, list):
            loop.run_until_complete(asyncio.wait(tasks))


class HttpServer:
    '''
    Tornado web server class.

    '''

    def __init__(self, router: Router = None,
                 ssl_options: Any = None, addresss: str = "",
                 options: AttrDict = None) -> None:
        env.setenv('CREATE_CONFIG', True)
        self.router = router
        self.ssl_options = ssl_options
        self.address = addresss
        self.application: Application = None
        self._conf_handlers = {}
        self._port = None
        self._conf_locale = False
        self.logger = None
        self.options = None
        self.conf = None
        self._init_options(options)
        self._init_config()

    def _init_options(self, options: AttrDict = None):
        if not options:
            self.options = CommandLine().parse_args()
        else:
            self.options = options
            for k, v in options.items():
                if TronadoStdout.has_opt(k):
                    TronadoStdout.set(k, v)
        enable_pretty_logging(AttrDict(TronadoStdout.getall()))

    def _init_config(self):
        from .config import conf
        self.conf = conf

    def _check_daemon(self):
        _daemon = self.conf.get_bool_option('setting', '_daemon', default=True)
        if self.options.daemon is False or _daemon is False:
            return False
        return True

    def _get_pid_path(self) -> str:
        if self.options.pid and not os.path.exists(self.options.pid):
            base_dir = os.path.dirname(self.options.pid)
            if os.access(base_dir, os.W_OK):
                return self.options.pid
        return os.path.join(strings.get_root_path(), 'server.pid')

    @staticmethod
    def _log_func(logger, handler: tornado.web.RequestHandler) -> None:
        if handler.get_status() < 400:
            log_method = logger.info
        elif handler.get_status() < 500:
            log_method = logger.warning
        else:
            log_method = logger.error
        req_time = 1000.0 * handler.request.request_time()
        log_method('%d %s %.2fms', handler.get_status(),
                   handler._request_summary(), req_time)

    @staticmethod
    def check_port(port: int, addr: str = '0.0.0.0', timeout: int = 1) -> bool:
        '''
        check port status

        :param port: `<int>`
        :param addr: `<str>` default 'localhost'
        :return: True -> used, False -> not used
        '''
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        code = sock.connect_ex((addr, port))
        sock.close()
        return True if code == 0 else False

    def configure_port(self) -> None:
        if not self.options.port or self.options.port <= 0:
            self._port = self.conf.get_int_option('setting', 'port', 8888)
        elif self.options.port > 65535:
            self._port = 8888
        else:
            self._port = self.options.port
        if self.check_port(self._port) and self.options.signal is None:
            self.logger.error(
                f'Server is running in http://localhost:{self._port}')
            sys.exit(1)

    def get_settings(self, settings_: dict = None) -> dict:
        '''Tornado settings'''
        debug = self.conf.get_bool_option('setting', '_debug', False)
        cookie_secret = self.conf.get_option('setting', 'cookie_secret',
                                             DEF_COOKIE_SECRET)
        data = default_settings(debug, cookie_secret=cookie_secret)
        if settings_:
            data.update(settings_)
        if 'log_function' not in data:
            data.update({'log_function': partial(self._log_func, self.logger)})
        return data

    def is_debug(self):
        if self.options.debug is True:
            return True
        if self.conf.get_bool_option('setting', '_debug', False):
            return True
        return False

    def process_signal(self, signalnum, frame):
        # received signal, stop server
        if signalnum != signal.SIGHUP:
            self.logger.error(
                f'Received system input signal: {signalnum}, closed server.')
            IOLoop.current().stop()
            sys.exit(1)
        else:
            SignalHandler.restart()

    def _signal_handler(self) -> bool:
        if self.options.signal:
            if self.options.signal not in SignalHandler.signals:
                self.logger.error(
                    'Error: signal options not in [restart, stop]')
                sys.exit(1)
            assert self._port, 'Please configure server port'
            if not self.check_port(self._port):
                return False
            pid_file = self._get_pid_path()
            return SignalHandler.signal_handler(
                pid_file, SignalHandler.signals[self.options.signal])
        return False

    def configure_daemon(self):
        # setting daemon, command line parameter first
        _pfile = self._get_pid_path()
        if self._check_daemon() is False:
            self.logger.info(f'Server pid [{os.getpid()}].')
            daemon.write_pid(_pfile, os.getpid())
            return
        daemon.fork(_pfile)
        self.logger.info(f'Server pid [{os.getpid()}].')

    def configure_locale(self,
                         locale_path: str = None,
                         locale_name: str = 'messages') -> None:
        '''Config internationalization.
        :param locale_path: `<str>` locale path base dir
        :param locale_name: `<str>` locale file name, default messages(.mo)
        :param lang: `<str>` default en_US (e.g: en_US/zh_CN)
        '''

        if locale_path and os.path.exists(locale_path):
            tornado.locale.set_default_locale(
                self.conf.get_option('setting', 'language', 'en_US'))
            tornado.locale.load_gettext_translations(locale_path, locale_name)
            self._conf_locale = True

    def configure_default_handler(self, handler: tornado.web.RequestHandler):
        self._conf_handlers['default_handler_class'] = handler

    def configure_static_handler(self, handler: tornado.web.RequestHandler):
        self._conf_handlers['static_handler_class'] = handler

    def configure_logger(self) -> None:
        from tweb.utils.log import logger
        self.logger = logger

    def configure_settings(self,
                           settings_: dict = None,
                           module: str = None) -> tuple:
        settings = self.get_settings(settings_)
        # setting default error handler or static file handler such as: 404
        if self._conf_handlers:
            settings.update(self._conf_handlers)
        modules = []
        if self.options.debug:
            settings['autoreload'] = True
            settings['debug'] = True
        else:
            settings['autoreload'] = settings['debug']
        modules = app.loading_handlers(name=module)
        return modules, settings

    def configure_http_server(self) -> None:
        if not self.application:
            self.logger.error('Please create application.')
            sys.exit(1)
        server = tornado.httpserver.HTTPServer(self.application,
                                               xheaders=True,
                                               ssl_options=self.ssl_options)
        if self.application.settings['debug'] is True:
            server.listen(self._port, address=self.address)
        else:
            sockets = tornado.netutil.bind_sockets(self._port,
                                                   address=self.address)
            if self.options.proc is None:
                proc = self.conf.get_int_option('setting',
                                                'processes',
                                                default=0)
            else:
                proc = self.options.proc
            tornado.process.fork_processes(proc)
            server.add_sockets(sockets)
        self.logger.info(f'Running on: http://localhost:{self._port}')

    def create_application(self, settings: dict, modules: list) -> Application:
        settings['server_port'] = self._port
        settings['server_host'] = socket.gethostname()
        settings['server_daemon'] = self._check_daemon()
        settings['server_debug'] = settings['debug']
        settings['server_config'] = self.options.conf
        settings['server_locale'] = self.conf.get_option(
            'setting', 'language', 'en_US')
        settings['server_conf_locale'] = self._conf_locale
        self.logger.info(f"Daemon mode: {settings['server_daemon']}")
        self.logger.info(f"Debug mode: {settings['debug']}")
        self.logger.info(f'Archive log: {self.logger.is_archive}')
        self.application = Application(modules, **settings)
        return self.application

    def initialize_tasks(self, tasks: Union[list] = None) -> None:
        if not tasks or not self.application:
            return
        _tasks = []
        for obj in tasks:
            argcount = obj['func'].__code__.co_argcount
            if argcount > 0:
                if isinstance(obj['func'], types.MethodType) and argcount == 1:
                    _func = obj['func']()
                else:
                    _func = obj['func'](*obj.get('args'), **obj.get('kwargs'))
            else:
                _func = obj['func']()
            if isinstance(_func, types.CoroutineType):
                _tasks.append(_func)
        self.application.init_with_loop(IOLoop.current().asyncio_loop, _tasks)
        self.logger.info('Initialize tasks done.')

    def start(self,
              settings: dict = None,
              tasks: Union[list] = None,
              module: str = None) -> None:
        self.configure_logger()
        self.configure_port()
        if self._signal_handler():
            return
        SignalHandler.listen(self.process_signal)
        self.configure_daemon()
        # self.configure_locale()
        modules, settings_ = self.configure_settings(settings, module)
        self.create_application(settings_, modules)
        self.configure_http_server()
        self.initialize_tasks(tasks)
        IOLoop.current().start()
