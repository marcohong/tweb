'''
Token class.

return dict, if state is True return success,
 otherwise, validate token fails.
message = {
    state:bool
    msg: str,
    data: dict
}

usage::

    from tweb.token import Token
    data = Token.create_token(1000,uid=1, username='tester')
    ret = Token.get_token(data)
'''
import time
import abc
import jwt
from typing import Any, Optional
import ujson
import tornado.web
from .config import conf
from tweb.utils.settings import DEF_COOKIE_SECRET

XTOKEN = conf.get_option('setting', 'cookie_secret_name', 'X-Token')
_SECRET = conf.get_option('setting', 'cookie_secret', DEF_COOKIE_SECRET)
_ENABLE_JWT = conf.get_option('setting', '_enable_jwt', True)


class AccessToken(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def create_token(cls,
                     expires: int,
                     secret: str = _SECRET,
                     **payload: Any) -> str:
        '''Create token

        :param expires: `<int>` expires times(seconds)
        :param secret: `<str>` default config sercet
        :param payload: `<Any>`
        :return: `<str>`
        '''

    @abc.abstractmethod
    def get_token(cls, value: str, secret: str = _SECRET) -> Optional[dict]:
        '''Get token

        :param value: `<str>`
        :param secret: `<str>` default config sercet
        :return: `<dict>` or None
        '''


class TornadoToken(AccessToken):
    @classmethod
    def create_token(cls,
                     expires: int,
                     secret: str = _SECRET,
                     **payload: Any) -> str:
        payload.update({'exp': int(time.time()) + expires})
        value = ujson.dumps(payload)
        ret = tornado.web.create_signed_value(secret, XTOKEN, value)
        return ret.decode('utf-8')

    @classmethod
    def get_token(cls, value: str, secret: str = _SECRET) -> Optional[dict]:
        ret = {'state': False, 'msg': 'Login timed out, please log in again'}
        if not value:
            return ret
        try:
            data = tornado.web.decode_signed_value(secret, XTOKEN, value)
            if not data:
                ret.update({'msg': 'Illegal token'})
                return ret
            data = ujson.loads(data)
            if float(data['exp']) < float(time.time()):
                ret.update({'msg': 'Token has expired'})
                return ret
            ret.update({
                'data': data,
                'state': True,
                'msg': 'Token authentication is successful'
            })
        except ValueError:
            ret['msg'] = 'Token authentication failure'
        return ret


CookieToken = TornadoToken


class JWTToken(AccessToken):
    headers = {'alg': 'HS256'}
    algorithm = 'HS256'

    @classmethod
    def create_token(cls,
                     expires: int,
                     _secret: str = _SECRET,
                     **payload: Any) -> str:
        payload.update({'iat': time.time(), 'exp': int(time.time()) + expires})
        ret = jwt.encode(payload,
                         _secret,
                         algorithm=cls.algorithm,
                         headers=cls.headers)
        return ret.decode('utf-8')

    @classmethod
    def get_token(cls, value: str, _secret: str = _SECRET) -> Optional[dict]:
        ret = {'state': False, 'msg': 'Login timed out, please log in again'}
        if not value:
            return ret
        try:
            ret['data'] = jwt.decode(value,
                                     _secret,
                                     algorithms=[cls.algorithm])
            ret['state'] = True
            ret['msg'] = 'Token authentication is successful'
        except KeyError:
            ret['msg'] = 'Invalid token secret'
        except jwt.exceptions.DecodeError:
            ret['msg'] = 'Token authentication failure'
        except jwt.exceptions.ExpiredSignatureError:
            ret['msg'] = 'Token has expired'
        except jwt.exceptions.InvalidTokenError:
            ret['msg'] = 'Illegal token'
        return ret


Token = JWTToken if _ENABLE_JWT else TornadoToken
