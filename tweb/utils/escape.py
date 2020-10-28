from typing import Any

try:
    import ujson as json
    JDecodeError = ValueError
except ImportError:
    import json
    JDecodeError = json.decoder.JSONDecodeError


class JsonDecodeError(JDecodeError):
    pass


def json_dumps(value: Any, sort_keys=None) -> str:
    return json.dumps(value, sort_keys=sort_keys)


def json_loads(value: Any) -> Any:
    return json.loads(value)
