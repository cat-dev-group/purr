from __future__ import annotations

from typing import Optional

from purr.http.headers import Headers


class HTTPResponse:
    """Base HTTP response object.

    Provides common functionality between the other HTTP
    response classes.
    """

    content_type: Optional[str] = None

    def __init__(
        self,
        body: Optional[bytes | str] = b"",
        *,
        status_code: int = 200,
        headers: Optional[Headers] = None,
        content_type: Optional[str] = None,
    ):
        if isinstance(body, str):
            body = body.encode("utf-8")

        self.body = body
        self.status_code = status_code
        self.headers: Headers = headers or Headers({})

        if content_type is not None:
            self.headers["content_type"] = content_type
