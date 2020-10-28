import os
import sys
import logging
from typing import Any, Union, Optional
from itertools import chain
from functools import partial
import importlib

from .exceptions import trace_info
from tweb.utils.single import SingleClass
'''
Tornado router.

usage:

from route import app, router

@router('/user/list')
class UserListHanler(tornado.web.RequestHandler):
    async def get(self):
        pass
# generator /user/list url

# or use app.register_module
user_router = app.register_module('user', url_prefix='/user')
@user_router('/list')
class UserListHanler(tornado.web.RequestHandler):
    async def get(self):
        pass
# generator /user/list url

tornado.web.Application(app.loading_handlers())
coding...

'''

allow_type = ['py', 'pyc', 'pyo', 'pyd', 'so']


class Router(SingleClass):
    # record public handlers
    _handlers = []
    # record handlers by moduel
    _modules = {}
    # moduel url prefix mapping
    _module_prefix = {}

    def register_module(self, name: str, url_prefix: str = None) -> callable:
        '''
        Register module, same like blueprint.

        :param name: `<str>` modeule name
        :param url_prefix: `<str>` url prefix
        :return:
        '''
        if not self._modules.get(name):
            self._modules[name] = []
            self._module_prefix[name] = url_prefix or ''

        def warpper(*url_patterns, groups=None):
            return self.router(name, *url_patterns, groups=groups)

        return warpper

    def register(self, url: str, handler: Any) -> None:
        '''
        Register handler to public handlers.

        :param url: `<str>`
        :param handler: `<tornado.web.HttpRequestHandler>`
        :return:
        '''
        self._handlers.append((url, handler))

    def router(self,
               module_name: str,
               *url_patterns: str,
               groups: Union[None, list, tuple] = None) -> None:
        '''
        Add tornado router.

        :param module_name: `<str>` module name if is None, save in _handlers.
        :param url_patterns: `<str>`

            e.g:router('api', '/list', '/users', groups=None)
                return ['/list','/list']
            If module_name is not none, [f'{url_prefix}/list',...]
        :param groups: `<list/tuple>`

            e.g:router('api', '/test', groups=('/v1','/v2'))
                return ['/v1/test','/v2/test']
            If module_name is not none, [f'{url_prefix}/v1/test',...]
        :return:
        '''
        def warpper(cls):
            _urls = list(url_patterns)
            if module_name and not self._modules.get(module_name):
                self._modules[module_name] = []
            special = [u for u in url_patterns if u.startswith('^')]
            if groups:
                _urls = [
                    g.strip() + u for u in url_patterns for g in groups
                    if not u.startswith('^')
                ]
            if hasattr(cls, 'url_prefix'):
                _urls = [cls.url_prefix + u for u in _urls]
            url_prefix = self._module_prefix.get(module_name)
            if url_prefix:
                _urls = [url_prefix + u for u in _urls]
            if special:
                _urls = _urls + [u[1:] for u in special]
            for url in _urls:
                if module_name:
                    self._modules[module_name].append((url, cls))
                else:
                    self._handlers.append((url, cls))

        return warpper

    def loading_handlers(self,
                         name: str = None,
                         with_public: bool = True) -> Optional[list]:
        '''
        Loading all handlers, if with_public return with public handlers.

        :param name: `<str>` module name
        :param with_public: `<bool>` with public handlers, default True
        :return: `<list>`
        '''
        if name:
            modules = self._modules.get(name, [])
        else:
            modules = list(chain(*self._modules.values()))
        if with_public:
            return modules + self._handlers
        return modules

    def _has_py_file(self, file_list: list):
        for file_ in file_list:
            if file_.split('.')[-1] in allow_type:
                return True
        return False

    def _get_file_path(self, path: str, files: list) -> list:
        file_list = os.listdir(path)
        if self._has_py_file(file_list):
            files.append(path)
        for file_ in file_list:
            curr_path = os.path.join(path, file_)
            if os.path.isdir(curr_path) and not file_.startswith('_'):
                self._get_file_path(curr_path, files)
            elif file_.split('.')[-1] in allow_type and file_.split(
                    '.')[0] != '__init__':
                files.append(curr_path)

        return files

    def _load_modules(self, files: set, base_dir: str) -> None:
        for file_ in files:
            file_ = file_.split('.')[0]
            module_path = file_[len(base_dir) + 1:].replace('/', '.')
            self._import_module(module_path)

    def _import_module(self, module: str) -> None:
        try:
            importlib.import_module(module)
        except ImportError:
            logging.error(trace_info())

    def auto_inject(self, ignore_dirs: Union[list] = None) -> None:
        start_shell = os.path.abspath(sys.argv[0])
        base_dir = os.path.dirname(start_shell)
        files = self._get_file_path(os.path.dirname(start_shell), [])
        files = set(files).difference(
            [start_shell, os.path.dirname(start_shell)])
        self._load_modules(files, base_dir)

    def inject_module(self, *module_bases: str) -> None:
        if not module_bases:
            return
        start_shell = os.path.abspath(sys.argv[0])
        base_dir = os.path.dirname(start_shell)
        paths = []
        for module_base in module_bases:
            _path = os.path.join(base_dir, module_base.replace('.', '/'))
            if os.path.exists(_path) and os.path.isdir(_path):
                paths.append(_path)

        files = []
        for path_ in paths:
            files.extend(self._get_file_path(path_, []))
        files = set(files)
        self._load_modules(files, base_dir)


app = Router()
router = partial(app.router, '')
