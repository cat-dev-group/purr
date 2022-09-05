"""Tests for the Router"""

from purr.routing.router import Route


def test_can_create_route():
    async def fn():
        pass

    route = Route(path="/fn", handler=fn)

    assert route.handler == fn
