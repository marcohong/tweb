from typing import Any, Awaitable, Callable, Optional
from tornado import httpclient
from tornado import simple_httpclient

from .exceptions import HTTPTimeoutError, HTTPError
from tweb.utils.escape import json_dumps


async def request(url: str,
                  *,
                  method: str = 'GET',
                  data: dict = None,
                  headers: dict = None,
                  timeout: int = None,
                  proxy: dict = None,
                  **kwargs: Any) -> Callable[..., Awaitable]:
    '''
    proxy
        proxy_host: str = None,
        proxy_port: int = None,
        proxy_username: str = None,
        proxy_password: str = None,
        proxy_auth_mode: str = None,
    '''
    kwargs['method'] = method
    kwargs['headers'] = headers
    kwargs['request_timeout'] = timeout
    kwargs['connect_timeout'] = timeout
    if proxy:
        kwargs = {**kwargs, **proxy}
    if data:
        body = '&'.join([f'{k}={v}' for k, v in data.items()])
        kwargs['body'] = body
    try:
        resp = await httpclient.AsyncHTTPClient().fetch(url, **kwargs)
    except simple_httpclient.HTTPTimeoutError as error:
        raise HTTPTimeoutError(error.code, error.message,
                               error.response) from error
    except httpclient.HTTPError as herr:
        raise HTTPError(herr.code, herr.message, herr.response) from herr
    else:
        return resp


def _build_headers(json: bool = False) -> dict:
    headers = {}
    headers['Accept-Language'] = 'zh-CN,zh;q=0.9,en-GB;q=0.8,en;q=0.7'
    headers['User-Agent'] = ("Mozilla/5.0 (Windows NT 6.3; WOW64)"
                             " Chrome/82.0.3396.99 Safari/537.36")
    if json:
        headers['Content-Type'] = 'application/json'
    return headers


async def post(url: str,
               data: dict = None,
               json: bool = False,
               timeout: int = None,
               **kwargs: Any) -> Optional[tuple]:
    '''Create http post request

    :param url: `<str>`
    :param data: `<dict>`
    :param json: `<bool>`
    :param timeout: `<int>`
    :param kwargs: `<dict>`
    :return: `<tuple>` status_code, body
    '''
    if not kwargs.get('headers'):
        kwargs['headers'] = _build_headers(json)
    elif json:
        kwargs['headers']['Content-Type'] = 'application/json'
    if json and data:
        kwargs['body'] = json_dumps(data)
    else:
        kwargs['data'] = data
    resp = await request(url, method='POST', timeout=timeout, **kwargs)
    if not resp:
        return None
    return resp.code, resp.body


async def get(url: str, timeout: int = None, **kwargs: Any) -> Optional[tuple]:
    '''Create http get request

    :param url: `<str>`
    :param timeout: `<int>`
    :param kwargs: `<dict>`
    :return: `<tuple>` status_code, body
    '''
    if not kwargs.get('headers'):
        kwargs['headers'] = _build_headers()
    resp = await request(url, method='GET', timeout=timeout, **kwargs)
    if not resp:
        return None
    return resp.code, resp.body
