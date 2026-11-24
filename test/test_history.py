from collections.abc import Callable
from datetime import UTC, datetime

import httpx2
import pytest

from gravitywell import AsyncPiHole, PiHole, PiHoleAuth
from gravitywell.models import TimeRange

BASE_URL = "http://pi.hole"
PASSWORD = "app-password"
# conftest.py's `serve` fixture.
type Serve = Callable[[object], httpx2.MockTransport]

# The live test Pi-hole's answers, cut to a few slots. In-memory slots are
# stamped at their middle (`...900`), database slots at their start (`...600`).
SLOT = 1795539900
ACTIVITY_BODY = {
    "history": [
        {"timestamp": SLOT - 600, "total": 0, "cached": 0, "blocked": 0, "forwarded": 0},
        {"timestamp": SLOT, "total": 43, "cached": 10, "blocked": 5, "forwarded": 28},
    ],
    "took": 0.0003,
}
CLIENT_ACTIVITY_BODY = {
    "history": [{"timestamp": SLOT, "data": {"192.168.1.235": 39, "others": 4}}],
    "clients": {
        "192.168.1.235": {"name": None, "total": 39},
        "others": {"name": "other clients", "total": 4},
    },
    "took": 0.0003,
}
DATABASE_ACTIVITY_BODY = {
    "history": [{"timestamp": 1795539600, "total": 43, "cached": 10, "blocked": 5, "forwarded": 28}],
    "took": 0.002,
}
DATABASE_CLIENT_ACTIVITY_BODY = {
    "history": [{"timestamp": 1795539600, "data": {"127.0.0.1": 4, "192.168.1.235": 39}}],
    "clients": {"127.0.0.1": {"name": "localhost", "total": 4}, "192.168.1.235": {"name": "", "total": 39}},
    "took": 0.002,
}
DAY = TimeRange(start=datetime(2026, 11, 24, tzinfo=UTC), until=datetime(2026, 11, 25, tzinfo=UTC))
DAY_PARAMS = {"from": "1795478400", "until": "1795564800"}


def test_activity_gets_history_and_reads_the_slots_as_times(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(ACTIVITY_BODY)) as api:
        history = api.history.activity().history

    slot = history[1]
    assert slot.timestamp == datetime.fromtimestamp(SLOT, tz=UTC)
    assert (slot.total, slot.cached, slot.blocked, slot.forwarded) == (43, 10, 5, 28)
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/history")


@pytest.mark.anyio
async def test_async_activity_gets_history(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(ACTIVITY_BODY)) as api:
        history = (await api.history.activity()).history

    assert len(history) == 2
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/history")


def test_clients_leaves_n_to_the_pi_hole_by_default(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(CLIENT_ACTIVITY_BODY)) as api:
        activity = api.history.clients()

    assert activity.clients["others"].name == "other clients"
    assert activity.history[0].data == {"192.168.1.235": 39, "others": 4}
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/history/clients")
    assert dict(request.url.params) == {}


@pytest.mark.anyio
async def test_async_clients_sends_count_as_n(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(CLIENT_ACTIVITY_BODY)) as api:
        await api.history.clients(count=0)

    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/history/clients")
    assert dict(request.url.params) == {"N": "0"}


def test_database_activity_sends_the_time_range(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(DATABASE_ACTIVITY_BODY)) as api:
        history = api.history.database.activity(DAY).history

    assert history[0].timestamp == datetime.fromtimestamp(1795539600, tz=UTC)
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/history/database")
    assert dict(request.url.params) == DAY_PARAMS


@pytest.mark.anyio
async def test_async_database_clients_sends_the_time_range(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(DATABASE_CLIENT_ACTIVITY_BODY)) as api:
        activity = await api.history.database.clients(DAY)

    assert (activity.clients["192.168.1.235"].name, activity.history[0].data["127.0.0.1"]) == ("", 4)
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/history/database/clients")
    assert dict(request.url.params) == DAY_PARAMS
