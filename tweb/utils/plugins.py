'''
Plugins loading.

usage:
    async def test1():
        ...

    def test2():
        ...

    plugins.register(test1)
    plugins.register(test2)
'''
import types
from collections import OrderedDict
from typing import Optional, Any

from tweb.utils.single import SingleClass
__all__ = ['plugins']


class Plugins(SingleClass):
    # {id:{func,args,kwargs}}
    _methods = OrderedDict()

    def register(self, func: callable, *args: Any, **kwargs: Any) -> None:
        '''
        Register plugin
        '''
        if not isinstance(func, (types.FunctionType, types.MethodType)):
            raise TypeError(f'{func} must be a function')
        self._methods[id(func)] = {
            'func': func,
            'args': args,
            'kwargs': kwargs
        }

    def unregister(self, func: callable) -> None:
        '''
        Remove plugin
        '''
        self._methods.pop(id(func), None)

    def loading(self) -> Optional[list]:
        '''
        Loading all plugins
        :return: list(tasks)
        '''
        return list(self._methods.values())


plugins = Plugins()
