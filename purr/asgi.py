from typing import Any, Awaitable, Callable, MutableMapping

ASGIScope = MutableMapping[str, Any]
ASGIMessage = MutableMapping[str, Any]
ASGISend = Callable[[ASGIMessage], Awaitable[None]]
ASGIReceive = Callable[[], Awaitable[ASGIMessage]]


class Purr:
    """The main ASGI application.

    An ASGI application
    """

    def __init__(self):
        pass

    async def __call__(self, scope: ASGIScope, receive: ASGIReceive, send: ASGISend):
        ...
