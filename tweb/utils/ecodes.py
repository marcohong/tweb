class HttpCodes(dict):
    http_100 = (100, 'Continue')
    http_101 = (101, 'Switching Protocols')
    http_102 = (102, 'Processing (WebDAV)')
    http_200 = (200, 'OK')
    http_201 = (201, 'Created')
    http_202 = (202, 'Accepted')
    http_203 = (203, 'Non-Authoritative Information')
    http_204 = (204, 'No Content')
    http_205 = (205, 'Reset Content')
    http_206 = (206, 'Partial Content')
    http_207 = (207, 'Multi-Status (WebDAV)')
    http_208 = (208, 'Already Reported (WebDAV)')
    http_226 = (226, 'IM Used')
    http_300 = (300, 'Multiple Choices')
    http_301 = (301, 'Moved Permanently')
    http_302 = (302, 'Found')
    http_303 = (303, 'See Other')
    http_304 = (304, 'Not Modified')
    http_305 = (305, 'Use Proxy')
    http_306 = (306, '(Unused)')
    http_307 = (307, 'Temporary Redirect')
    http_308 = (308, 'Permanent Redirect (experimental)')
    http_400 = (400, 'Bad Request')
    http_401 = (401, 'Unauthorized')
    http_402 = (402, 'Payment Required')
    http_403 = (403, 'Forbidden')
    http_404 = (404, 'Not Found')
    http_405 = (405, 'Method Not Allowed')
    http_406 = (406, 'Not Acceptable')
    http_407 = (407, 'Proxy Authentication Required')
    http_408 = (408, 'Request Timeout')
    http_409 = (409, 'Conflict')
    http_410 = (410, 'Gone')
    http_411 = (411, 'Length Required')
    http_412 = (412, 'Precondition Failed')
    http_413 = (413, 'Request Entity Too Large')
    http_414 = (414, 'Request-URI Too Long')
    http_415 = (415, 'Unsupported Media Type')
    http_416 = (416, 'Requested Range Not Satisfiable')
    http_417 = (417, 'Expectation Failed')
    http_418 = (418, 'I\'m a teapot (RFC 2324)')
    http_420 = (420, 'Enhance Your Calm (Twitter)')
    http_422 = (422, 'Unprocessable Entity (WebDAV)')
    http_423 = (423, 'Locked (WebDAV)')
    http_424 = (424, 'Failed Dependency (WebDAV)')
    http_425 = (425, 'Reserved for WebDAV')
    http_426 = (426, 'Upgrade Required')
    http_428 = (428, 'Precondition Required')
    http_429 = (429, 'Too Many Requests')
    http_431 = (431, 'Request Header Fields Too Large')
    http_444 = (444, 'No Response (Nginx)')
    http_449 = (449, 'Retry With (Microsoft)')
    http_450 = (450, 'Blocked by Windows Parental Controls (Microsoft)')
    http_451 = (451, 'Unavailable For Legal Reasons')
    http_499 = (499, 'Client Closed Request (Nginx)')
    http_500 = (500, 'Internal Server Error')
    http_501 = (501, 'Not Implemented')
    http_502 = (502, 'Bad Gateway')
    http_503 = (503, 'Service Unavailable')
    http_504 = (504, 'Gateway Timeout')
    http_505 = (505, 'HTTP Version Not Supported')
    http_506 = (506, 'Variant Also Negotiates (Experimental)')
    http_507 = (507, 'Insufficient Storage (WebDAV)')
    http_508 = (508, 'Loop Detected (WebDAV)')
    http_509 = (509, 'Bandwidth Limit Exceeded (Apache)')
    http_510 = (510, 'Not Extended')
    http_511 = (511, 'Network Authentication Required')


class ECodes(dict):
    success = (0, 'ok')
    fail = (1, 'fail')
    addr_not_found = (404, 'Address your visit does not exist')
    token_auth_success = (0, 'Token authentication is successful')
    login_timeout = (10001, 'Login timed out, please log in again')
    illegal_token = (10002, 'Illegal token')
    invalid_token_secret = (10003, 'Invalid token secret')
    token_expired = (10004, 'Token has expired')
    token_auth_fail = (10006, 'Token authentication failure')
