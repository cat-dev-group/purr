from purr._types import ASGIReceive, ASGIScope, ASGISend


class Purr:
    """The main ASGI application.

    An ASGI application
    """

    def __init__(self):
        pass

    async def __call__(self, scope: ASGIScope, receive: ASGIReceive, send: ASGISend):
        ...
