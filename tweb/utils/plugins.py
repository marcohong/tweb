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
from typing import Optional

from tweb.utils.single import SingleClass
__all__ = ['plugins']


class Plugins(SingleClass):
    # id:method/function
    _methods = {}

    def register(self, func: callable):
        '''
        Register plugin
        '''
        if not isinstance(func, (types.FunctionType, types.MethodType)):
            raise TypeError(f'{func} must be a function')
        self._methods[id(func)] = func

    def unregister(self, func: callable):
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
