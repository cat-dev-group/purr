from typing import Sequence, Optional

from purr._types import ASGIReceive, ASGIScope, ASGISend
from purr.routing import Route, Router


class Purr:
    """The main ASGI application.

    An ASGI application
    """

    def __init__(self, *, routes: Optional[Sequence[Route]] = None):
        self.router = Router(self, routes)

    async def __call__(self, scope: ASGIScope, receive: ASGIReceive, send: ASGISend):
        ...
