import io
import datetime
import logging
from typing import Union, Tuple, Optional, Any
import tornado.web
from xform.form import Form

from tweb.utils import strings
from tweb.response import DATA_TYPE, State, content
from tweb.utils.escape import json_dumps
from tweb.utils.settings import CORS_HEADERS
# from tweb.utils.log import logger
from .exceptions import trace_info, Error


class BaseHandler(tornado.web.RequestHandler):
    err_resp_only_json: bool = False
    # router define, list object
    url_pattern: str = None

    def initialize(self):
        pass

    def on_finish(self):
        pass

    async def prepare(self):
        self.set_cors_header()

    @property
    def client_ip(self) -> str:
        '''Nginx setting X-Real-IP and X-Forwarded-For'''
        return self.request.remote_ip

    def lang(self, message: str) -> str:
        return self.locale.translate(message)

    def get_user_locale(self, cookie_name: str = 'locale') -> Optional[str]:
        locale = self.get_cookie(cookie_name)
        if locale:
            return tornado.locale.get(locale)
        return tornado.locale.get(self.settings['server_locale'])

    def get_chs_cookie(self,
                       name: str,
                       default: Union[None, str] = None) -> Optional[str]:
        result = super().get_cookie(name, default=default)
        return result.encode('latin1').decode('utf8') if result else None

    def set_chs_cookie(self,
                       name: str,
                       value: Union[str, bytes],
                       *,
                       domain: str = None,
                       expires: Union[float, Tuple, datetime.datetime] = None,
                       path: str = "/",
                       expires_days: int = None,
                       **kwargs: Any) -> None:
        if strings.is_chinese(value):
            value = value.encode('utf-8').decode('latin1')
        super().set_cookie(name,
                           value,
                           domain=domain,
                           expires=expires,
                           path=path,
                           expires_days=expires_days,
                           **kwargs)

    async def get(self, *args, **kwargs):
        self.set_status(404)
        self.page_not_found()

    async def options(self, *args: Any, **kwargs: Any):
        self.write('')

    async def form_validate(self,
                            form: Form,
                            msg: str = 'The content submitted is incorrect',
                            _raise: bool = True,
                            locations: Union[str, tuple] = None) -> dict:
        '''Form validation.

        usage::

            form = SubmitForm(
                id=field.Integer(required=True)
            )
            data = awiat self.form_validate(form)
            #or
            try:
                data = await self.form_validate(form)
            except tornado.web.HTTPError as err:
                self.failure(msg=self.lang(err.message), data=err.error)
            #or
            data, error = await self.form_validate(form, _raise=False)

        :param form: `<Form>`
        :param msg: `<str>`
        :param _raise: `<bool>` raise exception, default `True`
        :return: `<dict>` data
        :raise HTTPError:
        '''
        data, error = await form.bind(self, locations=locations)
        if error:
            if _raise:
                self.form_error = {'msg': self.lang(msg), 'error': error}
                raise tornado.web.HTTPError(400, msg)
        return data

    def success(self,
                msg: str = None,
                data: DATA_TYPE = None,
                **kwargs: Any) -> None:
        '''
        Write success message to browser.
        '''
        self.process(State.SUCCESS.value, msg, data, **kwargs)

    def failure(self,
                msg: str = None,
                data: DATA_TYPE = None,
                **kwargs) -> None:
        '''
        Write failure message to browser.
        '''
        self.process(State.FAILED.value, msg, data, **kwargs)

    def jsonify(self, **kwargs: Any) -> None:
        self.finish(json_dumps(kwargs))

    def string(self, text: str) -> None:
        self.finish(text)

    def files(self, filename: str, stream: io.BytesIO) -> None:
        '''
        Download file.

        usage::

            stream = io.BytesIO()
            stream.write('test'.encode('utf8'))
            #or
            stream = io.BytesIO('test'.encode('utf8'))

        :param filename: `<str>` file name
        :param stream: `<BytesIO>` stream object
        '''
        self.set_stream_header(filename)
        stream.seek(0, 0)
        while 1:
            data = stream.read(4096)
            if not data:
                break
            self.write(data)
        stream.close()
        self.finish()

    def stream(self, stream: io.BytesIO, content_type: str) -> None:
        '''
        Output file, e.g: qrcode

        :param stream: `<BytesIO>` stream object
        :param content_type: `<str>` e.g: image/jpg
        :return:
        '''
        self.set_header('Content-Type', content_type)
        self.finish(stream.getvalue())

    def page_not_found(self, url: str = None) -> None:
        self.process(404, url=url)

    def write_error(self, status_code: int, **kwargs: Any) -> None:
        '''
        Write error result.

        :param status_code: `<int>`
            e.g 400 401 403 404 405 500 (10001 no login error code)
            if user defined code, must be more than 4 characters.
        :param kwargs: `<dict>`
            exc_info: `<tuple>` tornado exception info
            log_record: `<bool>` record stderr, default True
            msg: `<str>` if has message
            url: `<str>` error template path, if not url, self write message
        '''
        exc_info = kwargs.pop('exc_info', None)
        if not self.settings['debug'] and kwargs.get('log_record', True):
            if not exc_info or not \
                    isinstance(exc_info[1], (tornado.web.HTTPError, Error)):
                logging.error(trace_info())
        # 表单错误特殊处理
        if exc_info:
            if isinstance(exc_info[1], Error):
                self.set_status(200)
                _msg = content(State.FAILED.value,
                               msg=self.lang(exc_info[1].message))
            else:
                if hasattr(self,
                           'form_error') and exc_info[1].status_code == 400:
                    self.set_status(200)
                    _msg = content(State.FAILED.value,
                                   msg=self.form_error['msg'],
                                   error=self.form_error['error'])
                else:
                    _msg = content(
                        State.FAILED.value,
                        msg=self.lang('Server to open a small guess'))

        else:
            self.set_status(status_code)
            _msg = content(status_code,
                           msg=kwargs.get('msg')
                           or self.lang('Server to open a small guess'))

        if strings.req_is_json(self.request) or self.err_resp_only_json:
            self.set_json_header()
            self.finish(json_dumps(_msg['data']))
        else:
            url = kwargs.get('url')
            if not url:
                self.set_header('Content-Type', 'text/plain;charset=UTF-8')
                self.finish(json_dumps(_msg['data']))
            else:
                self.render_html(url, data=_msg['data'])

    def process(self,
                state: int,
                msg: str = None,
                data: DATA_TYPE = None,
                url: str = None,
                **kwargs: Any) -> None:
        '''
        Process server write json data to client.
        cannot used @callback
        '''
        _msg = content(state=state, msg=msg, data=data, **kwargs)
        if url:
            self.render_html(url, data=_msg['data'])
        else:
            self.set_json_header()
            self.finish(json_dumps(_msg['data']))

    def render_html(self, template_name: str, **kwargs: Any) -> None:
        '''
        renader html
        '''
        self.render(template_name, **kwargs)

    def set_cors_header(self) -> None:
        '''
        fixed ajax cross-domain request problem
        '''
        if not self.settings.get('cors'):
            return
        if self.settings.get('access_control_allow_origin'):
            self.set_header('Access-Control-Allow-Origin',
                            self.settings['cors'])
        for key, val in CORS_HEADERS.items():
            self.set_header(key, val)

    def set_json_header(self) -> None:
        '''
        set json header
        '''
        self.set_header('Content-Type', 'application/json;charset=UTF-8')

    def set_stream_header(self, filename: str) -> None:
        '''Set strem header

         usage::

            self.set_stream_header('user.csv')
            self.write('id,name,age')
            ...
        '''
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition',
                        f'attachment;filename={filename}')
        self.set_header('Cache-Control', 'No-cache')


class DefaultHandler(BaseHandler):
    '''
    Tornado default error handler, can not delete.
    '''

    html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>Error</title>
</head>
<body>
    {msg}
</body>
</html>
    '''

    async def get(self):
        if strings.req_is_json(self.request) or self.err_resp_only_json:
            self.process(404,
                         msg=self.lang('Address your visit does not exist'))
        else:
            self.set_header('Content-Type', 'text/html')
            data = self.html_template.format(
                msg=self.lang('Address your visit does not exist'))
            self.finish(data)
