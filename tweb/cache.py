import aredis
from redis.sentinel import Sentinel
from typing import Any, Optional, Union, Awaitable

from .config import Config
from .exceptions import NotFoundError
from tweb.utils.attr_util import AttrDict
from tweb.utils.log import logger


class Cache:
    '''
    Create redis cache calss.

    usage::

    url = 'redis://localhost:6379/0'
    cache = Cache(url).initialize()
    '''
    def __init__(self,
                 address,
                 conf_prefix: str = None,
                 is_sentinel: bool = False,
                 decode_responses=True,
                 **kwargs: Any):
        '''
        redis init

        :param address: `<str/list>` url or [(ip,port),...]
            if is_sentinel is True, address = [(ip,port),...]
        :param conf_prefix: `<str>` priority: address > conf_prefix
            e.g: user_redis_url -> MemRedis(conf_prefix='user')
            if is_sentinel is True, deprecated.
        :param is_sentinel: `<bool>` default False
        :param kwargs: `<Any>` redis connection kwargs
        :return:
        '''
        self.cache = None
        self.address = address
        self.is_sentinel = is_sentinel
        if is_sentinel:
            self._redis = Sentinel
        else:
            self._redis = aredis.StrictRedis.from_url
        self.conf_prefix = conf_prefix
        kwargs.update({'decode_responses': decode_responses})
        self.kwargs = kwargs

    def initialize(self):
        # web service before start init
        if self.address:
            self.cache = self._redis(self.address, **self.kwargs)
            logger.debug(f'Init redis connection from {self.address}')
        elif self.conf_prefix and not self.is_sentinel:
            url = Config().get_option('redis',
                                      f'{self.conf_prefix}_redis_url',
                                      default=None)
            assert url, f'{self.conf_prefix}_redis_url config does not exist'
            self.cache = self._redis(url, **self.kwargs)
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
                                         str]) -> Awaitable[Optional[str]]:
        data = await cls.get(key)
        if not data:
            raise NotFoundError
        return data

    @classmethod
    def set(cls,
            key: str,
            value: Any,
            *,
            ex=None,
            px=None,
            nx=False,
            xx=False) -> Awaitable[bool]:
        return cls.cache.set(key, value, ex=ex, px=px, nx=nx, xx=xx)

    @classmethod
    def get(cls, key: Union[int, str]) -> Awaitable[str]:
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
                                         int]) -> Awaitable[Optional[dict]]:
        data = await cls.get(id_)
        if not data:
            raise NotFoundError
        return data

    @classmethod
    async def get(cls, id_: Union[str, int]) -> Awaitable[Optional[dict]]:
        if not id_:
            return None
        data = await cls._get(cls._get_key(id_))
        return AttrDict(cls._get_convert(data)) if data else None

    @classmethod
    async def get_cache(cls, **kwargs: Any) -> Awaitable[Optional[dict]]:
        data = await cls._get(cls._get_dkey(**kwargs))
        return AttrDict(cls._get_convert(data)) if data else None

    @classmethod
    def _get(cls, _key: str) -> Awaitable[Optional[dict]]:
        return cls.cache.hgetall(_key)

    @classmethod
    def _set(cls, _key: str, **kwargs: Any) -> Awaitable[bool]:
        return cls.cache.hmset(_key, kwargs)

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
    def set(cls, id_: Union[str, int], **kwargs: Any) -> Awaitable[bool]:
        kwargs = cls._set_filter(kwargs)
        return cls._set(cls._get_key(id_), **kwargs)

    @classmethod
    def set_cache(cls, **kwargs: Any) -> Awaitable[bool]:
        kwargs = cls._set_filter(kwargs)
        return cls._set(cls._get_dkey(**kwargs), **kwargs)

    @classmethod
    def remove(cls, id_: Union[int, str]) -> Awaitable[int]:
        return cls.cache.delete(cls._get_key(id_))

    @classmethod
    def removes(cls, *ids_: Union[int, str]) -> Awaitable[int]:
        keys = [cls._get_key(_id) for _id in ids_]
        return cls.cache.delete(*keys)

    @classmethod
    def remove_cache(cls, **kwargs: Any) -> Awaitable[int]:
        return cls.cache.delete(cls._get_dkey(**kwargs))

    @classmethod
    def remove_key(cls, id_: Union[int, str],
                   *keys: Union[int, str]) -> Awaitable[int]:
        return cls.cache.hdel(cls._get_key(id_), *keys)
