import copy
import base64
import hashlib
import crypt
from typing import Optional, Union
from tweb.utils.strings import get_rand_str


def _encode_utf8(text) -> str:
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
    assert isinstance(text, str)
    text = _encode_utf8(text)
    return hashlib.md5(text).hexdigest()


def sha1(text: str) -> str:
    '''
    Encrypt text to md5.
    '''
    assert isinstance(text, str)
    text = _encode_utf8(text)
    return hashlib.sha1(text).hexdigest()


def encrypt(text: str, length: int = 32) -> str:
    '''
    simple encrypt.
    min chr(65) A
    max chr(126) ~
    '''
    _ba = bytearray(str(text[::-1]).encode('utf-8'))
    _len = len(_ba)
    _ca = bytearray(_len * 4)
    _nt = 0
    for i in range(0, _len):
        _b1 = _ba[i]
        _b2 = _b1 ^ length
        _c1 = _b2 % 16
        _c2 = _b2 // 16
        _c1 = _c1 + 65
        _c2 = _c2 + 65  # _b2 = _c2 * 16 + _c1
        _c3 = abs(_c1 - _c2) + 65
        _c4 = _c1 + _c2
        if _c4 > 61:
            _c4 = (_c4 - 61) // 16 + 65
        _ca[_nt] = _c1
        _ca[_nt + 1] = _c3
        _ca[_nt + 2] = _c2
        _ca[_nt + 3] = _c4

        _nt += 4
    return _ca.decode('utf-8')[::-1]


def decrypt(text: int, length: int = 32) -> Optional[str]:
    '''
    simple decrypt
    '''
    if isinstance(text, bytes):
        text = text.decode('utf-8')
    _ba = bytearray(str(text[::-1]).encode('utf-8'))
    _len = len(_ba)
    if _len % 4 != 0:
        return None
    _len = _len // 4
    _ca = bytearray(_len)
    _nt = 0
    for i in range(0, _len):
        _c1 = _ba[_nt]
        _c2 = _ba[_nt + 2]
        _nt += 4
        _c1 = _c1 - 65
        _c2 = _c2 - 65
        _b2 = _c2 * 16 + _c1
        _b1 = _b2 ^ length
        _ca[i] = _b1
    try:
        return _ca.decode('utf-8')[::-1]
    except Exception:
        return None


def hex_passwd(text: str) -> str:
    '''
    Encrypt password.

    :param text: `<str>` password text
    '''
    etype = 'md5'
    salt = get_rand_str(6)
    hsh = get_hexdigest(etype, salt, text)
    return f'{etype}${salt}${hsh}'


def check_passwd(user_password: str, raw_password: str):
    '''
    Check password.
    :param user_password: `<str>` user password
    :param raw_password: `<str>` input raw password
    :returns: True pass
    '''
    if '$' not in user_password:
        return False
    algo, salt, hsh = user_password.split('$')
    return hsh == get_hexdigest(algo, salt, raw_password)


def get_hexdigest(etype: str, salt: str, text: str) -> str:
    '''
    Encrypt text.

    :param etype: `<str>` md5/sha1/crypt
    :param salt: `<str>` salt, e.g: random 6-digit string
    :param text: `<str>`  encrypt text
    '''
    if etype == 'crypt':
        return crypt.crypt(text, salt)
    elif etype == 'md5':
        return md5(salt + text)
    elif etype == 'sha1':
        return sha1(salt + text)
    raise ValueError('Got unknown password encrypt type in password.')


# -----------------------------signature begin------------------------------- #
def _sort_hash_data(data, pop_keys: Union[list, tuple] = None) -> str:
    _data = copy.copy(data)
    if pop_keys is not None:
        for key in pop_keys:
            _data.pop(key, None)
    _data = sorted(_data.items(), key=lambda x: x[0])
    return '&'.join(['%s=%s' % x for x in _data])


def create_hexdigest_sign(data: dict,
                          secret_key: str,
                          sign_key: str = 'sign') -> str:
    '''Create hexdigest sign.

    :param data: `<dict>` sign data
    :param secret_key: `<str>`
    :param sign_key: `<str>`
    :raise ValueError:
    :return: `<str>` sign value
    '''
    if not data or not secret_key:
        raise ValueError('Parameter data or secret_key is required')
    sort_str = _sort_hash_data(data, (sign_key, ))
    unsign_str = f'{sort_str}&key={secret_key}'
    return md5(unsign_str)


def create_hexdigest_data(data: dict,
                          secret_key: str,
                          sign_key: str = 'sign') -> dict:
    '''Create hexdigest data.

    :param data: `<dict>` sign data
    :param secret_key: `<str>`
    :param sign_key: `<str>`
    :raise ValueError:
    :return: `<dict>` sign data
    '''
    sign_str = create_hexdigest_sign(data, secret_key, sign_key=sign_key)
    return {**data, **{sign_key: sign_str}}


def validate_hexdigest_sign(data: dict,
                            secret_key: str,
                            sign_key: str = 'sign') -> bool:
    '''Validate hexdigest sign.

    :param data: `<dict>` sign data
    :param secret_key: `<str>`
    :param sign_key: `<str>`
    :raise ValueError:
    :return: `<bool>` True -> success, else False
    '''
    assert sign_key in data, 'sign is required'
    sign_val = create_hexdigest_sign(data, secret_key, sign_key=sign_key)
    req_sign_val = data[sign_key]
    return sign_val == req_sign_val
