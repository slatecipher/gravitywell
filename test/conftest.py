from collections.abc import Callable

import httpx2
import pytest

# What `serve`'s transport answers PiHoleAuth's logins and logouts with.
SESSION_BODY = {"session": {"sid": "sid-1"}, "took": 0.003}


@pytest.fixture
def anyio_backend() -> str:
    # Run async tests on asyncio only. anyio 4.10, the lowest version
    # `pyproject.toml` allows, runs them on trio too by default, even though
    # trio isn't installed.
    return "asyncio"


@pytest.fixture
def sent() -> list[httpx2.Request]:
    """The requests `serve`'s transport got, other than logins and logouts."""
    return []


@pytest.fixture
def serve(sent: list[httpx2.Request]) -> Callable[[object], httpx2.MockTransport]:
    """Make transports that answer like a Pi-hole.

    `serve(body)` answers each login and logout, and every other request with
    `body`, which it records in `sent`. Test modules can't import from here, so
    each one names the type: `type Serve = Callable[[object], MockTransport]`.
    """

    def transport(body: object) -> httpx2.MockTransport:
        def handler(request: httpx2.Request) -> httpx2.Response:
            if request.url.path == "/api/auth":
                return httpx2.Response(200, json=SESSION_BODY)
            sent.append(request)
            return httpx2.Response(200, json=body)

        return httpx2.MockTransport(handler)

    return transport
