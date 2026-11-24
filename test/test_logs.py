from collections.abc import Callable
from datetime import UTC, datetime

import httpx2
import pytest

from gravitywell import AsyncPiHole, PiHole, PiHoleAuth

BASE_URL = "http://pi.hole"
PASSWORD = "app-password"
# conftest.py's `serve` fixture.
type Serve = Callable[[object], httpx2.MockTransport]


def log_body(*messages: str, prio: str | None = None) -> dict[str, object]:
    return {
        "log": [
            {"timestamp": 1795547056.5 + i, "message": message, "prio": prio} for i, message in enumerate(messages)
        ],
        "nextID": 154,
        "pid": 187,
        "file": "/var/log/pihole/FTL.log",
        "took": 0.0003,
    }


@pytest.mark.anyio
@pytest.mark.parametrize("name", ["dnsmasq", "ftl", "webserver"])
async def test_each_log_method_reads_its_own_log(name: str, serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(log_body("started"))) as api:
        response = await getattr(api.logs, name)()

    assert (response.next_id, response.pid, response.log[0].message) == (154, 187, "started")
    assert response.log[0].timestamp == datetime.fromtimestamp(1795547056.5, tz=UTC)
    [request] = sent
    assert (request.method, request.url.path, dict(request.url.params)) == ("GET", f"/api/logs/{name}", {})


def test_next_id_is_sent_as_next_id_in_camel_case(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(log_body())) as api:
        assert api.logs.dnsmasq(next_id=150).log == []

    [request] = sent
    assert dict(request.url.params) == {"nextID": "150"}


def test_lines_keeps_the_newest_lines_and_next_id(serve: Serve) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(log_body("one", "two", "three"))) as api:
        response = api.logs.webserver(lines=2)

    assert ([line.message for line in response.log], response.next_id) == (["two", "three"], 154)


def test_session_ids_are_redacted_in_every_form_ftl_logs_them(serve: Serve) -> None:
    # The lines in FTL v6.9's source that can hold a session ID, and one that
    # only looks like it.
    messages = (
        'Read sid="Fk3BjL0Ij9mJ1lFy0HaG5A==" from header',
        "Cannot bind sid = Fk3BjL0Ij9mJ1lFy0HaG5A== in backup_db_sessions(): disk I/O error (10)",
        "Requested API URI: 192.168.1.2 -> GET /api/stats/summary ? sid=Fk3BjL0Ij9mJ1lFy0HaG5A%3D%3D (Content-Type )",
        'ACCESS: 192.168.1.2 - - "GET /api/stats/summary?full=true&sid=Fk3BjL0Ij9mJ1lFy0HaG5A%3D%3D HTTP/1.1" 200',
        "setsid failed: Operation not permitted",
    )
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(log_body(*messages, prio="DEBUG_API"))) as api:
        log = api.logs.ftl().log

    assert [line.message for line in log] == [
        'Read sid="<redacted>" from header',
        "Cannot bind sid = <redacted> in backup_db_sessions(): disk I/O error (10)",
        "Requested API URI: 192.168.1.2 -> GET /api/stats/summary ? sid=<redacted> (Content-Type )",
        'ACCESS: 192.168.1.2 - - "GET /api/stats/summary?full=true&sid=<redacted> HTTP/1.1" 200',
        "setsid failed: Operation not permitted",
    ]
