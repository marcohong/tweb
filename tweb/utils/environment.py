# current process env
from typing import Optional
from tweb.utils.strings import get_root_path
from tweb.utils.single import SingleClass

__all__ = ['Environment', 'env']


class Environment(SingleClass):
    _env: dict = {'ROOT_PATH': get_root_path()}

    def getenv(self, name: str) -> Optional[str]:
        return self._env.get(name)

    def setenv(self, name: str, value: str) -> None:
        self._env[name] = value


env = Environment()
