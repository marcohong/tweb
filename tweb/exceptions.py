import sys
import traceback


def trace_info() -> str:
    # traceback.format_exc()
    ret = traceback.format_exception(*sys.exc_info())
    return ''.join([r.lstrip() for r in ret])


class Error(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)

    def __repr__(self):
        return self.message

    __str__ = __repr__


class FormError(Error):
    def __init__(self, message: str, error: dict = None) -> None:
        self.message = message
        self.error = error
        super().__init__(message)


class NotFoundError(Error):
    def __init__(self, message: str = 'Record does not exist') -> None:
        self.message = message
        super().__init__(message)


class ValidatorError(Error):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class OperateError(Error):
    pass


class UploadError(OperateError):
    pass


class InsertError(OperateError):
    pass


class UpdateError(OperateError):
    pass


class DeleteError(OperateError):
    pass
