from __future__ import annotations

import asyncio
import inspect
import re
import functools

from typing import Optional, Pattern, Sequence, Callable, Any

from purr.http.responses import HTTPResponse
from purr._types import ASGIScope, ASGISend, ASGIReceive


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


class Route:
    """Represents a route.

    Represents a route made up of a path and its corresponding
    handler.
    """

    def __init__(self, path: str, handler: Callable[[Any], Any], method: str = "get"):
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
