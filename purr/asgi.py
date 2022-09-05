from typing import Sequence, Optional, Callable, TypeVar, Any
from typing_extensions import ParamSpec  # Backwards compatibility

from purr._types import ASGIReceive, ASGIScope, ASGISend
from purr.routing import Route, Router


T = TypeVar("T")
P = ParamSpec("P")


class Purr:
    """The main ASGI application.

    An ASGI application
    """

    def __init__(self, *, routes: Optional[Sequence[Route]] = None):
        self.router = Router(self, routes)

    async def __call__(self, scope: ASGIScope, receive: ASGIReceive, send: ASGISend):
        await self.router(scope, receive, send)

    def route(self, path: str, method: str = "get") -> Callable[..., Any]:
        """A decorator for registering new routes.

        Args:
            path (str): The path for the route.
            method (str, optional): The route's HTTP method. Defaults to "get"

        Returns:
            Callable[..., Any]: A decorator.
        """

        def decorator(func: Callable[P, T]) -> Callable[P, T]:
            self.router.register(path, func, method)
            return func

        return decorator
