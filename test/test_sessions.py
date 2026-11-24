from collections.abc import Callable
from datetime import UTC, datetime

import httpx2
import pytest
from clientx.tools import list_tools

from gravitywell import AsyncPiHole, PiHole, PiHoleAuth

BASE_URL = "http://pi.hole"
PASSWORD = "app-password"
# conftest.py's `serve` fixture.
type Serve = Callable[[object], httpx2.MockTransport]


def session(session_id: int, *, current: bool, app: bool, user_agent: str | None) -> dict[str, object]:
    return {
        "id": session_id,
        "current_session": current,
        "valid": True,
        "tls": {"login": False, "mixed": False},
        "login_at": 1795540000,
        "last_active": 1795540300,
        "valid_until": 1795542100,
        "remote_addr": "192.168.1.235",
        "user_agent": user_agent,
        "x_forwarded_for": None,
        "app": app,
        "cli": False,
    }


SESSIONS_BODY = {
    "sessions": [
        session(0, current=False, app=False, user_agent="Mozilla/5.0"),
        session(2, current=True, app=True, user_agent=None),
    ],
    "took": 0.0001,
}


def test_list_reads_who_logged_in_and_when(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(SESSIONS_BODY)) as api:
        sessions = api.sessions.list().sessions

    assert [(s.id, s.current_session, s.app, s.user_agent) for s in sessions] == [
        (0, False, False, "Mozilla/5.0"),
        (2, True, True, None),
    ]
    assert sessions[0].login_at == datetime.fromtimestamp(1795540000, tz=UTC)
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/auth/sessions")


@pytest.mark.anyio
async def test_async_delete_deletes_a_session_by_its_number(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve({})) as api:
        await api.sessions.delete(3)

    [request] = sent
    assert (request.method, request.url.path) == ("DELETE", "/api/auth/session/3")


def test_ai_tools_mark_listing_read_only_and_deleting_destructive() -> None:
    tools = {tool.name: tool for tool in list_tools(PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD)))}

    assert (tools["sessions_list"].read_only, tools["sessions_delete"].destructive) == (True, True)
