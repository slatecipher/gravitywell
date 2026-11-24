from collections.abc import Callable
from datetime import UTC, datetime

import httpx2
import pytest

from gravitywell import AsyncPiHole, PiHole, PiHoleAuth
from gravitywell.models import SummaryResponse

BASE_URL = "http://pi.hole"
PASSWORD = "app-password"
# conftest.py's `serve` fixture.
type Serve = Callable[[object], httpx2.MockTransport]
LAST_UPDATE = 1795533826

# A test Pi-hole's answer after a few dozen queries, with the breakdowns cut
# short.
SUMMARY_BODY = {
    "queries": {
        "total": 43,
        "blocked": 5,
        "percent_blocked": 11.627906799316406,
        "unique_domains": 15,
        "forwarded": 28,
        "cached": 10,
        "frequency": 1.2,
        "types": {"A": 17, "AAAA": 7, "HTTPS": 4, "OTHER": 0},
        "status": {"GRAVITY": 5, "FORWARDED": 28, "CACHE": 10, "REGEX": 0},
        "replies": {"IP": 19, "BLOB": 11, "NXDOMAIN": 4},
    },
    "clients": {"active": 2, "total": 2},
    "gravity": {"domains_being_blocked": 81677, "last_update": LAST_UPDATE},
    "took": 0.0002,
}


def assert_read(summary: SummaryResponse) -> None:
    queries = summary.queries
    assert (queries.total, queries.blocked, queries.forwarded, queries.cached) == (43, 5, 28, 10)
    assert queries.status["GRAVITY"] == 5
    assert (summary.clients.active, summary.gravity.domains_being_blocked) == (2, 81677)
    assert summary.gravity.last_update == datetime.fromtimestamp(LAST_UPDATE, tz=UTC)


def test_summary_gets_stats_summary_and_reads_the_totals(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(SUMMARY_BODY)) as api:
        assert_read(api.stats.summary())

    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/stats/summary")


@pytest.mark.anyio
async def test_async_summary_gets_stats_summary_and_reads_the_totals(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(SUMMARY_BODY)) as api:
        assert_read(await api.stats.summary())

    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/stats/summary")


def test_a_last_update_of_zero_reads_as_unknown(serve: Serve) -> None:
    body = {**SUMMARY_BODY, "gravity": {"domains_being_blocked": 0, "last_update": 0}}

    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(body)) as api:
        assert api.stats.summary().gravity.last_update is None
