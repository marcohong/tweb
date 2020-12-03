import sys
import traceback
from typing import Any


def trace_info() -> str:
    # traceback.format_exc()
    ret = traceback.format_exception(*sys.exc_info())
    return ''.join([r.lstrip() for r in ret])


class Error(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)

    def __str__(self):
        return f'Error message: {self.message}'

    __repr__ = __str__


class FormError(Error):
    def __init__(self, message: str, error: dict = None) -> None:
        self.error = error
        super().__init__(message)


class RespError(Error):
    def __init__(self, code: int, message: str) -> None:
        self.code = code
        super().__init__(message)

    def __str__(self):
        return f'<code:{self.code}, message:{self.message}>'

    __repr__ = __str__


class NotFoundError(RespError):
    def __init__(self,
                 code: int = 404,
                 message: str = 'Record does not exist') -> None:
        super().__init__(code, message)


class ValidatorError(RespError):
    def __init__(self, code: int, message: str) -> None:
        super().__init__(code, message)


class OperateError(RespError):
    def __init__(self, code: int, message: str) -> None:
        super().__init__(code, message)


class UploadError(OperateError):
    pass


class InsertError(OperateError):
    pass


class UpdateError(OperateError):
    pass


class DeleteError(OperateError):
    pass


class HTTPError(RespError):
    def __init__(self, code: int, message: str = None, response: Any = None):
        self.response = response
        super().__init__(code, message)


class HTTPTimeoutError(HTTPError):
    pass
