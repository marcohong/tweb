import copy
import base64
import hashlib
import hmac
from typing import Union


def _encode_utf8(text: Union[str, bytes]) -> bytes:
    if not isinstance(text, bytes):
        return text.encode('utf-8')
    return text


def b64encode(text: str, encoding: str = 'utf8') -> Union[str, bytes]:
    rest = base64.b64encode(_encode_utf8(text))
    return rest.decode(encoding=encoding)


def b64decode(text: str, encoding: str = 'utf8') -> Union[str, bytes]:
    rest = base64.b64decode(_encode_utf8(text))
    return rest.decode(encoding=encoding)


def urlsafe_encode(text: str, encoding: str = 'utf8') -> Union[str, bytes]:
    rest = base64.urlsafe_b64encode(_encode_utf8(text))
    return rest.decode(encoding=encoding)


def urlsafe_decode(text: str, encoding: str = 'utf8') -> Union[str, bytes]:
    rest = base64.urlsafe_b64decode(_encode_utf8(text))
    return rest.decode(encoding=encoding)


def md5(text: str) -> str:
    '''
    Encrypt text to sha1.
    '''
    text = _encode_utf8(text)
    return hashlib.md5(text).hexdigest()


def sha1(text: str) -> str:
    '''
    Encrypt text to sha1.
    '''
    text = _encode_utf8(text)
    return hashlib.sha1(text).hexdigest()


def sha256(text: str) -> str:
    '''
    Encrypt text to sha256.
    '''
    text = _encode_utf8(text)
    return hashlib.sha256(text).hexdigest()


def hmac_message(text: str, secret: str, digestmod='md5') -> str:
    ret = hmac.new(_encode_utf8(secret),
                   _encode_utf8(text), digestmod=digestmod)
    return ret.hexdigest()

# -----------------------------signature begin------------------------------- #


def _sort_hash_data(data,
                    pop_keys: Union[list, tuple] = None,
                    reverse: bool = False) -> str:
    _data = copy.copy(data)
    if pop_keys is not None:
        for key in pop_keys:
            _data.pop(key, None)
    _data = sorted(_data.items(), key=lambda x: x[0], reverse=reverse)
    return '&'.join(['%s=%s' % x for x in _data])


def create_hexdigest_sign(data: dict,
                          secret_key: str,
                          sign_key: str = 'sign',
                          secret_name: str = 'key',
                          reverse: bool = False) -> str:
    '''Create hexdigest sign.

    :param data: `<dict>` sign data
    :param secret_key: `<str>`
    :param sign_key: `<str>`
    :param secret_name: `<str>` secret_key name
    :param reverse: `<bool>`
    :raise ValueError:
    :return: `<str>` sign value
    '''
    if not data or not secret_key:
        raise ValueError('Parameter data or secret_key is required')
    sort_str = _sort_hash_data(data, pop_keys=(sign_key, ), reverse=reverse)
    unsign_str = f'{sort_str}&{secret_name}={secret_key}'
    return md5(unsign_str)


def create_hexdigest_data(data: dict,
                          secret_key: str,
                          sign_key: str = 'sign',
                          secret_name: str = 'key',
                          reverse: bool = False) -> dict:
    '''Create hexdigest data.

    :param data: `<dict>` sign data
    :param secret_key: `<str>`
    :param sign_key: `<str>`
    :param secret_name: `<str>` secret_key name
    :param reverse: `<bool>`
    :raise ValueError:
    :return: `<dict>` sign data
    '''
    sign_val = create_hexdigest_sign(data,
                                     secret_key,
                                     sign_key=sign_key,
                                     secret_name=secret_name,
                                     reverse=reverse)
    return {**data, **{sign_key: sign_val}}


def validate_hexdigest_sign(data: dict,
                            secret_key: str,
                            sign_key: str = 'sign',
                            secret_name: str = 'key',
                            reverse: bool = False) -> bool:
    '''Validate hexdigest sign.

    :param data: `<dict>` sign data
    :param secret_key: `<str>`
    :param sign_key: `<str>`
    :param secret_name: `<str>` secret_key name
    :param reverse: `<bool>`
    :raise ValueError:
    :return: `<bool>` True -> success, else False
    '''
    assert sign_key in data, 'sign is required'
    sign_val = create_hexdigest_sign(data,
                                     secret_key,
                                     sign_key=sign_key,
                                     secret_name=secret_name,
                                     reverse=reverse)
    req_sign_val = data[sign_key]
    return sign_val == req_sign_val
