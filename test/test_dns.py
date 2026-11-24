import json
from typing import Any

import httpx2
import pytest
from clientx.tools import list_tools

from gravitywell import AsyncPiHole, PiHole, PiHoleAuth

BASE_URL = "http://pi.hole"
PASSWORD = "app-password"
# What the auth's login and logout get, around the endpoint's request.
SESSION_BODY = {"session": {"sid": "sid-1"}, "took": 0.003}
BLOCKING_BODY = {"blocking": "disabled", "timer": 299.5, "took": 0.0001}


def serve(body: dict[str, Any], sent: list[httpx2.Request]) -> httpx2.MockTransport:
    def handler(request: httpx2.Request) -> httpx2.Response:
        if request.url.path == "/api/auth":
            return httpx2.Response(200, json=SESSION_BODY)
        sent.append(request)
        return httpx2.Response(200, json=body)

    return httpx2.MockTransport(handler)


def test_blocking_gets_dns_blocking_and_reads_the_status_and_timer() -> None:
    sent: list[httpx2.Request] = []

    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(BLOCKING_BODY, sent)) as api:
        status = api.dns.blocking()

    assert (status.blocking, status.timer) == ("disabled", 299.5)
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/dns/blocking")


@pytest.mark.anyio
async def test_async_blocking_gets_dns_blocking_and_reads_the_status_and_timer() -> None:
    sent: list[httpx2.Request] = []

    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(BLOCKING_BODY, sent)) as api:
        status = await api.dns.blocking()

    assert (status.blocking, status.timer) == ("disabled", 299.5)
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/dns/blocking")


def test_blocking_reads_failure_which_ftl_sends_though_its_spec_says_failed() -> None:
    body = {"blocking": "failure", "timer": None, "took": 0.0001}

    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(body, [])) as api:
        assert api.dns.blocking().blocking == "failure"


# A timer is sent only when given: without one, the change is permanent.
SET_BLOCKING_CASES = [
    ({"blocking": False, "timer": 300}, {"blocking": False, "timer": 300}),
    ({"blocking": True}, {"blocking": True}),
]


@pytest.mark.parametrize(("arguments", "sent_body"), SET_BLOCKING_CASES)
def test_set_blocking_posts_the_status_and_any_timer(arguments: dict[str, Any], sent_body: dict[str, Any]) -> None:
    sent: list[httpx2.Request] = []

    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(BLOCKING_BODY, sent)) as api:
        status = api.dns.set_blocking(**arguments)

    assert status.blocking == "disabled"
    [request] = sent
    assert (request.method, request.url.path) == ("POST", "/api/dns/blocking")
    assert json.loads(request.content) == sent_body


@pytest.mark.anyio
@pytest.mark.parametrize(("arguments", "sent_body"), SET_BLOCKING_CASES)
async def test_async_set_blocking_posts_the_status_and_any_timer(
    arguments: dict[str, Any], sent_body: dict[str, Any]
) -> None:
    sent: list[httpx2.Request] = []

    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(BLOCKING_BODY, sent)) as api:
        status = await api.dns.set_blocking(**arguments)

    assert status.blocking == "disabled"
    [request] = sent
    assert (request.method, request.url.path) == ("POST", "/api/dns/blocking")
    assert json.loads(request.content) == sent_body


def test_ai_tools_mark_set_blocking_destructive_and_idempotent() -> None:
    tools = {tool.name: tool for tool in list_tools(PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD)))}

    set_blocking = tools["dns_set_blocking"]
    assert (set_blocking.read_only, set_blocking.destructive, set_blocking.idempotent) == (False, True, True)
    assert tools["dns_blocking"].read_only
