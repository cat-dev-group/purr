from __future__ import annotations

from typing import Optional

from purr.http.headers import Headers
from purr._types import ASGIScope, ASGIReceive, ASGISend


class HTTPResponse:
    """Base HTTP response object.

    Provides common functionality between the other HTTP
    response classes.

    Args:
        body: The body of the response. Defaults to None.
        status_code: The status code of the response. Defaults to 200.
        headers: The response headers. Defaults to None.
        content_type: The content type of the response. Defaults to None.

    Attributes:
        body: The body of the response.
        status_code: The status code of the response.
        headers: The response headers.
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
            self.headers["Content-Type"] = content_type

    async def __call__(self, _scope: ASGIScope, _receive: ASGIReceive, send: ASGISend):
        await send({"type": "http.response.start", "status": self.status_code, "headers": self.headers.raw()})

        await send({"type": "http.response.body", "body": self.body})
