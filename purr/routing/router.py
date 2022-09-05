from __future__ import annotations

import inspect
import re
from typing import Any, Callable, Pattern, Sequence, TypeVar
from urllib.parse import parse_qs

from pydantic import ValidationError, create_model, parse_obj_as
from typing_extensions import ParamSpec  # Backwards compatibility

from purr._types import ASGIApp, ASGIReceive, ASGIScope, ASGISend
from purr.http.responses import HTTPResponse

METHODS = {
    "get",
    "post",
    "delete",
    "put",
    "head",
    "connect",
    "options",
    "trace",
    "patch",
}

PATH_REGEX = re.compile(r"{([a-zA-Z_][a-zA-Z\d_]*)}")  # The regex for matching path parameters in a url


def get_path_params(path: str) -> list[str]:
    """Extract path parameters from a path.

    Args:
        path (str): The path to extract from

    Returns:
        list[str]: A list of path parameters.
    """

    path_params: list[str] = []

    for match in PATH_REGEX.finditer(path):
        param_name: str = match.group()[1:-1]  # The name of the path parameter
        path_params.append(param_name)

    return path_params


def compile_path_regex(path: str, path_params: list[str], method: str) -> Pattern[str]:
    """Compile a regex that matches the given path.

    Args:
        path (str): The path to compile the regex for.
        path_params (list[str]): A list of path parameters for the path.
        method (str): The HTTP method which the route accepts.

    Returns:
        Pattern: A regex pattern which matches the given path.
    """

    pattern = f"{method}_{path}"

    for param in path_params:
        pattern = pattern.replace(
            f"{{{param}}}", rf"(?P<{param}>[a-zA-Z_0-9]+)"
        )  # Replace the path parameter with a regex group for matching it

    return re.compile(pattern)


def parse_params(
    query_params: dict[str, str], path_params: dict[str, str], types: dict[str, str]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Parses query and path parameters to their corresponding types.

    Args:
        query_params (dict[str, str]): A dictionary containing query parameters and their values.
        path_params (dict[str, str]): A dictionary containing path parameters and their values.
        types (dict[str, str]): A dictionary containing the types to cast the query and path parameters to.

    Returns:
        tuple[dict[str, Any], dict[str, Any]]: A tuple of two dicts which contains the parsed query
        and path parameters.

    Raises:
        ValidationError: Raises pydantic's ValidationError upon encountering an invalid value which
        cannot be parsed.
    """

    # Parses the parameters using a dictionary comprehension. `k` is the current
    # key in the original parameters dictionary, and `v` is the value to be casted.
    # The function fetches a type from `types` corresponding to the current key,
    # and if there isn't one, uses Any for casting, which effectively doesn't cast.
    parsed_q = {k: parse_obj_as(create_model(types.get(k) or "Any"), v) for k, v in query_params.items()}
    parsed_p = {k: parse_obj_as(create_model(types.get(k) or "Any"), v) for k, v in path_params.items()}

    return parsed_q, parsed_p


class Route:
    """Represents a route.

    Represents a route made up of a path and its corresponding
    handler.
    """

    def __init__(self, path: str, handler: Callable[..., Any], method: str = "get"):
        if not inspect.iscoroutinefunction(handler):
            raise AttributeError("Handler must be an asynchronous function")

        self.path = path
        self.handler = handler

        # If the given request method isn't in the global METHODS set, raise an error.
        if method.lower() not in METHODS:
            raise AttributeError(f"Invalid request method {method}")

        self.method = method.lower()
        self.path_params = get_path_params(path)  # Get the path parameters for the path.
        self.path_regex = compile_path_regex(
            path, self.path_params, method
        )  # Compiled regex which matches the route's path.

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Route):
            return False

        return self.path == other.path and self.method == other.method


T = TypeVar("T")
P = ParamSpec("P")


class Router:
    """Managed and dispatches routes for a purr application.

    Wraps an ASGI app and dispatches routes to their corresponding handlers.

    Args:
        app: An ASGI application.
        routes: A sequence of routes to create the Router with.

    Attributes:
        routes: The router's dictionary of routes.
        app: An ASGI application.
    """

    def __init__(self, app: ASGIApp, routes: Sequence[Route] | None = None):
        if routes is None:
            routes = []
        self.routes = {route.path_regex: route for route in routes}
        self.app = app

    def register(self, path: str, handler: Callable[..., Any], method: str = "get") -> None:
        """Register a route.

        Args:
            path (str): The path for the route.
            handler (Callable[[Any], Any]): The handler for the route.
            method (str, optional): The route's HTTP method. Defaults to "get".
        """

        route = Route(path, handler, method)
        self.routes[route.path_regex] = route

    def route(self, path: str, method: str = "get") -> Callable[..., Any]:
        """A decorator for registering new routes.

        Args:
            path (str): The path for the route.
            method (str, optional): The route's HTTP method. Defaults to "get"

        Returns:
            Callable[P, T]: A decorator.
        """

        def decorator(func: Callable[P, T]) -> Callable[P, T]:
            self.register(path, func, method)
            return func

        return decorator

    async def __call__(self, scope: ASGIScope, receive: ASGIReceive, send: ASGISend) -> None:
        if scope["type"] not in ("http", "websocket"):
            # If request type isn't HTTP or websocket, return an error.
            response = HTTPResponse(f"Invalid request type {scope['type']}", status_code=400)
            await response(scope, receive, send)
            return

        if "router" not in scope:
            scope["router"] = self

        for pattern, route in self.routes.items():
            match = pattern.match(scope["path"])
            if match:
                if scope["method"].lower() != route.method:
                    response = HTTPResponse("Method not allowed", status_code=405)
                    await response(scope, receive, send)
                    return

                path_params: dict[str, str] = match.groupdict()
                query_params: dict[str, str] = {k.decode(): v[0] for k, v in parse_qs(scope["query_string"]).items()}

                # Try to parse parameters if types are annotated.
                if route.handler.__annotations__:
                    try:
                        handler_annotations = {k: str(v) for k, v in route.handler.__annotations__}
                        query_params, path_params = parse_params(query_params, path_params, handler_annotations)
                    except ValidationError as e:
                        # If the type conversion failed, return an error
                        response = HTTPResponse(
                            f"Bad request, failed to parse parameters: {e.errors()[0]['msg']}", status_code=400
                        )
                        await response(scope, receive, send)
                        return

                try:
                    response = await route.handler(*path_params.values(), **query_params)
                except ValidationError as e:
                    response = HTTPResponse("Missing required query parameters", status_code=422)

                await response(scope, receive, send)
                return

        response = HTTPResponse("URL not found", status_code=404)
        await response(scope, receive, send)
