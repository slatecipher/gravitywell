import json
from typing import Any

import anyio
import httpx2
import pytest

from gravitywell import AsyncPiHole, PiHole, PiHoleAuth

BASE_URL = "http://pi.hole"
PASSWORD = "app-password"
WRONG_PASSWORD = "wrong-password"

VERSION_BODY = {
    "version": {name: {"local": {"version": "v6.1"}} for name in ("core", "web", "ftl")},
    "took": 0.0003,
}

type Call = tuple[str, str, str | None]


def session_body(sid: str | None, *, valid: bool = True) -> dict[str, Any]:
    session = {"valid": valid, "totp": False, "sid": sid, "csrf": None, "validity": 1800, "message": None}
    return {"session": session, "took": 0.003}


class FakePiHole:
    """Answers like a Pi-hole: each login issues a new session ID, `sid-1`,
    `sid-2`..., and other requests need a live one, unless there's no password.
    """

    def __init__(self, *, has_password: bool = True) -> None:
        self.has_password = has_password
        self.sent: list[httpx2.Request] = []
        # Recorded on arrival: a request sent again after a 401 is the same
        # object, with a new session header.
        self.received: list[Call] = []
        self.live: set[str] = set()
        self.logins = 0

    def __call__(self, request: httpx2.Request) -> httpx2.Response:
        self.sent.append(request)
        self.received.append((request.method, request.url.path, request.headers.get("X-FTL-SID")))
        if (request.method, request.url.path) == ("POST", "/api/auth"):
            if not self.has_password:
                return httpx2.Response(200, json=session_body(None))
            if json.loads(request.content) != {"password": PASSWORD}:
                return httpx2.Response(401, json=session_body(None, valid=False))
            self.logins += 1
            sid = f"sid-{self.logins}"
            self.live.add(sid)
            return httpx2.Response(200, json=session_body(sid))

        sid = request.headers.get("X-FTL-SID")
        if self.has_password and sid not in self.live:
            return httpx2.Response(401, json=session_body(None, valid=False))
        if request.method == "DELETE":
            self.live.discard(sid or "")
            return httpx2.Response(204)
        return httpx2.Response(200, json=VERSION_BODY)

    def calls(self) -> list[Call]:
        return self.received


def client(fake: FakePiHole, password: str = PASSWORD) -> PiHole:
    return PiHole(BASE_URL, auth=PiHoleAuth(password), transport=httpx2.MockTransport(fake))


LOGIN: Call = ("POST", "/api/auth", None)


def version(sid: str | None) -> Call:
    return ("GET", "/api/info/version", sid)


def test_the_first_request_logs_in_and_sends_the_session() -> None:
    fake = FakePiHole()

    client(fake).info.version()

    assert fake.calls() == [LOGIN, version("sid-1")]
    login = fake.sent[0]
    assert json.loads(login.content) == {"password": PASSWORD}
    assert login.headers["User-Agent"].startswith("gravitywell/")


def test_later_requests_reuse_the_session() -> None:
    fake = FakePiHole()
    api = client(fake)

    api.info.version()
    api.info.version()

    assert fake.calls() == [LOGIN, version("sid-1"), version("sid-1")]


def test_a_401_logs_in_again_and_resends_the_request() -> None:
    fake = FakePiHole()
    api = client(fake)
    api.info.version()
    fake.live.clear()  # The session expired.

    api.info.version()

    assert fake.calls() == [LOGIN, version("sid-1"), version("sid-1"), LOGIN, version("sid-2")]


def test_a_second_401_raises_without_logging_in_again() -> None:
    fake = FakePiHole()

    def always_unauthorized(request: httpx2.Request) -> httpx2.Response:
        response = fake(request)
        return response if request.url.path == "/api/auth" else httpx2.Response(401)

    api = PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=httpx2.MockTransport(always_unauthorized))

    with pytest.raises(httpx2.HTTPStatusError) as raised:
        api.info.version()

    assert raised.value.response.status_code == 401
    assert fake.logins == 2


def test_a_failed_login_raises_with_the_login_response() -> None:
    fake = FakePiHole()

    with pytest.raises(httpx2.HTTPStatusError) as raised:
        client(fake, password=WRONG_PASSWORD).info.version()

    assert raised.value.response.request.url.path == "/api/auth"
    assert raised.value.response.json()["session"]["valid"] is False
    assert fake.calls() == [LOGIN]


def test_a_pi_hole_without_a_password_gets_no_session_header() -> None:
    fake = FakePiHole(has_password=False)
    api = client(fake)

    api.info.version()
    api.info.version()

    assert fake.calls() == [LOGIN, version(None), version(None)]


@pytest.mark.parametrize("close", ["with", "close"])
def test_closing_logs_out(close: str) -> None:
    fake = FakePiHole()
    api = client(fake)

    if close == "with":
        with api:
            api.info.version()
    else:
        api.info.version()
        api.close()

    assert fake.calls()[-1] == ("DELETE", "/api/auth", "sid-1")
    assert fake.live == set()


def test_closing_without_a_session_sends_nothing() -> None:
    fake = FakePiHole()

    client(fake).close()

    assert fake.sent == []


def test_a_failed_logout_is_ignored() -> None:
    fake = FakePiHole()

    def unreachable_on_logout(request: httpx2.Request) -> httpx2.Response:
        if request.method == "DELETE":
            raise httpx2.ConnectError("unreachable", request=request)
        return fake(request)

    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=httpx2.MockTransport(unreachable_on_logout)) as api:
        api.info.version()


def async_client(fake: FakePiHole) -> AsyncPiHole:
    async def slow_login(request: httpx2.Request) -> httpx2.Response:
        # Gives concurrent requests the chance to log in at the same time.
        if request.url.path == "/api/auth":
            await anyio.sleep(0.01)
        return fake(request)

    return AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=httpx2.MockTransport(slow_login))


@pytest.mark.anyio
async def test_the_async_flow_logs_in_and_again_after_a_401() -> None:
    fake = FakePiHole()
    api = async_client(fake)

    await api.info.version()
    fake.live.clear()  # The session expired.
    await api.info.version()

    assert fake.calls() == [LOGIN, version("sid-1"), version("sid-1"), LOGIN, version("sid-2")]


@pytest.mark.anyio
async def test_concurrent_async_requests_share_one_login() -> None:
    fake = FakePiHole()
    api = async_client(fake)

    async with anyio.create_task_group() as tasks:
        for _ in range(5):
            tasks.start_soon(api.info.version)

    assert fake.logins == 1


@pytest.mark.anyio
@pytest.mark.parametrize("close", ["with", "close"])
async def test_async_closing_logs_out(close: str) -> None:
    fake = FakePiHole()
    api = async_client(fake)

    if close == "with":
        async with api:
            await api.info.version()
    else:
        await api.info.version()
        await api.aclose()

    assert fake.calls()[-1] == ("DELETE", "/api/auth", "sid-1")
    assert fake.live == set()
