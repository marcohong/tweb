'''
Redis cache base classes.
'''
import aioredis
from typing import Any, Callable, Union, Awaitable

from .config import Config
from .exceptions import NotFoundError
from tweb.utils.attr_util import AttrDict
from tweb.utils.log import logger
__all__ = ['MemRedis', 'StrCache', 'DictCache']


async def create_redis_pool(address,
                            *,
                            db=None,
                            password=None,
                            ssl=None,
                            encoding=None,
                            minsize=1,
                            maxsize=10,
                            timeout=None,
                            loop=None) -> Callable[..., None]:
    return await aioredis.create_redis_pool(address,
                                            db=db,
                                            password=password,
                                            ssl=ssl,
                                            encoding=encoding,
                                            minsize=minsize,
                                            maxsize=maxsize,
                                            timeout=timeout,
                                            loop=loop)


async def create_sentinel_pool(sentinels: Union[list, tuple],
                               master: str,
                               *,
                               db=None,
                               password=None,
                               encoding=None,
                               minsize=1,
                               maxsize=10,
                               ssl=None,
                               parser=None,
                               loop=None) -> Callable[..., None]:
    conn = await aioredis.sentinel.create_sentinel_pool(sentinels,
                                                        db=db,
                                                        password=password,
                                                        encoding=encoding,
                                                        minsize=minsize,
                                                        maxsize=maxsize,
                                                        ssl=ssl,
                                                        parser=parser,
                                                        loop=loop)
    conn.master_for(master)
    return conn


class MemRedis:
    '''
    Create redis cache calsses.
    '''
    def __init__(self,
                 address: Union[str, tuple, list] = None,
                 conf_prefix: str = None,
                 is_sentinel: bool = False,
                 strict: bool = True,
                 **kwargs):
        '''
        redis init

        :param address: `<str/tuple/list>`
            if is_sentinel is True, address = [(ip,port),...]
        :param conf_prefix: `<str>` priority: address > conf_prefix
            e.g: user_redis_url -> MemRedis(conf_prefix='user')
            if is_sentinel is True, deprecated.
        :param is_sentinel: `<bool>` default False
        :param strict: `<bool>` redis strict, default True
        :param kwargs: `<Any>` redis connection kwargs
        :return:
        '''
        self.cache = None
        self.strict = strict
        self.address = address
        self.is_sentinel = is_sentinel
        if is_sentinel:
            self.create_pool = create_sentinel_pool
        else:
            self.create_pool = create_redis_pool
        self.conf_prefix = conf_prefix
        self.kwargs = kwargs

    async def initialize(self):
        # web service before start init
        if self.address:
            self.cache = await self.create_pool(self.address, **self.kwargs)
            logger.debug(f'Init redis connection from {self.address}')
        elif self.conf_prefix:
            url = Config().get_option('redis',
                                      f'{self.conf_prefix}_redis_url',
                                      default=None)
            assert url, f'{self.conf_prefix}_redis_url config does not exist'
            self.cache = await create_redis_pool(url, **self.kwargs)
            logger.debug(f'Init redis connection from {url}')
        return self

    def __getattr__(self, name):
        return getattr(self.cache, name)

    def __getitem__(self, name):
        return self.cache[name]

    def __setitem__(self, name, value):
        self.cache[name] = value

    def __delitem__(self, name):
        del self.cache[name]


class StrCache:
    cache = None

    @classmethod
    async def get_or_404(cls, key: Union[int,
                                         str]) -> Callable[..., Awaitable]:
        data = await cls.get(key)
        if not data:
            raise NotFoundError
        return data

    @classmethod
    def set(cls,
            key: str,
            value: Any,
            *,
            expire: int = 0,
            pexpire: int = 0,
            exist: Any = None):
        return cls.cache.set(key,
                             value,
                             expire=expire,
                             pexpire=pexpire,
                             exist=exist)

    @classmethod
    def get(cls, key: Union[int, str]) -> Callable[..., Awaitable]:
        return cls.cache.get(str(key))


class DictCache:
    cache = None
    __rdskey__: str = 'default:dict:{0}'
    # ignore fields
    __filters__: tuple = None
    # convert fields mapping, bool use DictCache._bool
    __cvt_base_keys__: dict = {'id': int}
    # user define convert fields
    __cvt_keys__: dict = {}

    @staticmethod
    def _bool(val: str) -> bool:
        if not val or val.lower() == 'false':
            return False
        return False

    @staticmethod
    def _list(val: str) -> list:
        if not val or not (val.startswith('[') and val.endswith(']')):
            return None
        return eval(val)

    @staticmethod
    def _tuple(val: str) -> tuple:
        if not val or not (val.startswith('(') and val.endswith(')')):
            return None
        return eval(val)

    @classmethod
    def _get_key(cls, key: int) -> str:
        return cls.__rdskey__.format(key)

    @classmethod
    def _get_dkey(cls, **kwargs: Any) -> str:
        return cls.__rdskey__.format(**kwargs)

    @staticmethod
    def attr_dict(data):
        return AttrDict(data)

    @classmethod
    async def get_or_404(cls, id_: Union[str,
                                         int]) -> Callable[..., Awaitable]:
        data = await cls.get(id_)
        if not data:
            raise NotFoundError
        return data

    @classmethod
    async def get(cls, id_: Union[str, int]) -> Callable[..., Awaitable]:
        if not id_:
            return None
        data = await cls._get(cls._get_key(id_))
        return AttrDict(cls._get_convert(data)) if data else None

    @classmethod
    async def get_cache(cls, **kwargs: Any) -> Callable[..., Awaitable]:
        data = await cls._get(cls._get_dkey(**kwargs))
        return AttrDict(cls._get_convert(data)) if data else None

    @classmethod
    def _get(cls, _key: str) -> Callable[..., Awaitable]:
        return cls.cache.hgetall(_key)

    @classmethod
    def _set(cls, _key: str, **kwargs: Any) -> Callable[..., Awaitable]:
        return cls.cache.hmset_dict(_key, **kwargs)

    @classmethod
    def _get_convert(cls, data: dict) -> dict:
        _keys = {**cls.__cvt_base_keys__, **cls.__cvt_keys__}
        for _key, _type in _keys.items():
            if not callable(_type):
                continue
            if isinstance(_key, tuple):
                for key in _key:
                    if data.get(key):
                        data.update({key: _type(data[key])})
            else:
                if data.get(_key):
                    data.update({_key: _type(data[_key])})
        return data

    @classmethod
    def _set_filter(cls, kwargs: dict, replace_none: bool = True) -> dict:
        if cls.__filters__:
            kwargs = {
                k: v
                for k, v in kwargs.items() if k not in cls.__filters__
            }
        if replace_none:
            kwargs = {
                k: str(v) if v is not None else ''
                for k, v in kwargs.items()
            }
        return kwargs

    @classmethod
    def set(cls, id_: Union[str, int],
            **kwargs: Any) -> Callable[..., Awaitable]:
        kwargs = cls._set_filter(kwargs)
        return cls._set(cls._get_key(id_), **kwargs)

    @classmethod
    def set_cache(cls, **kwargs: Any) -> Callable[..., Awaitable]:
        kwargs = cls._set_filter(kwargs)
        return cls._set(cls._get_dkey(**kwargs), **kwargs)

    @classmethod
    def remove(cls, id_: Union[int, str]) -> Callable[..., Awaitable]:
        return cls.cache.delete(cls._get_key(id_))

    @classmethod
    def removes(cls, *ids_: Union[int, str]) -> Callable[..., Awaitable]:
        keys = [cls._get_key(_id) for _id in ids_]
        return cls.cache.delete(*keys)

    @classmethod
    def remove_cache(cls, **kwargs: Any) -> Callable[..., Awaitable]:
        return cls.cache.delete(cls._get_dkey(**kwargs))

    @classmethod
    def remove_key(cls, id_: Union[int, str],
                   key: Union[int, str]) -> Callable[..., Awaitable]:
        return cls.cache.hdel(cls._get_key(id_), key)
