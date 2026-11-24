from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import httpx2
import pytest

from gravitywell import AsyncPiHole, PiHole, PiHoleAuth
from gravitywell.models import SummaryResponse, TimeRange

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


TOP_DOMAINS_BODY = {
    "domains": [{"domain": "example.com", "count": 8}, {"domain": "github.com", "count": 7}],
    "total_queries": 43,
    "blocked_queries": 5,
    "took": 0.0001,
}
TOP_CLIENTS_BODY = {
    "clients": [{"name": "", "ip": "192.168.1.50", "count": 39}, {"name": "localhost", "ip": "127.0.0.1", "count": 4}],
    "total_queries": 43,
    "blocked_queries": 5,
    "took": 0.0001,
}


def test_top_domains_gets_permitted_domains_by_default(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(TOP_DOMAINS_BODY)) as api:
        top = api.stats.top_domains()

    assert [(item.domain, item.count) for item in top.domains] == [("example.com", 8), ("github.com", 7)]
    assert (top.total_queries, top.blocked_queries) == (43, 5)
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/stats/top_domains")
    assert dict(request.url.params) == {"blocked": "false", "count": "10"}


@pytest.mark.anyio
async def test_async_top_domains_sends_blocked_and_count(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(TOP_DOMAINS_BODY)) as api:
        top = await api.stats.top_domains(blocked=True, count=2)

    assert top.domains[0].domain == "example.com"
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/stats/top_domains")
    assert dict(request.url.params) == {"blocked": "true", "count": "2"}


def test_top_clients_gets_clients_by_all_queries_by_default(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(TOP_CLIENTS_BODY)) as api:
        top = api.stats.top_clients()

    assert [(item.ip, item.name, item.count) for item in top.clients] == [
        ("192.168.1.50", "", 39),
        ("127.0.0.1", "localhost", 4),
    ]
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/stats/top_clients")
    assert dict(request.url.params) == {"blocked": "false", "count": "10"}


@pytest.mark.anyio
async def test_async_top_clients_sends_blocked_and_count(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(TOP_CLIENTS_BODY)) as api:
        top = await api.stats.top_clients(blocked=True, count=1)

    assert top.clients[0].ip == "192.168.1.50"
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/stats/top_clients")
    assert dict(request.url.params) == {"blocked": "true", "count": "1"}


def test_totals_of_minus_one_read_as_hidden_by_the_privacy_level(serve: Serve) -> None:
    body = {"domains": [], "total_queries": -1, "blocked_queries": -1, "took": 0.0001}

    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(body)) as api:
        top = api.stats.top_domains()

    assert (top.domains, top.total_queries, top.blocked_queries) == ([], None, None)


# The live test Pi-hole's answers.
UPSTREAMS_BODY = {
    "upstreams": [
        {"ip": "blocklist", "name": "blocklist", "port": -1, "count": 5, "statistics": {"response": 0, "variance": 0}},
        {"ip": "cache", "name": "cache", "port": -1, "count": 10, "statistics": {"response": 0, "variance": 0}},
        {
            "ip": "8.8.4.4",
            "name": "dns.google",
            "port": 53,
            "count": 28,
            "statistics": {"response": 0.016012964248657228, "variance": 0.0017079313165119022},
        },
    ],
    "total_queries": 43,
    "forwarded_queries": 28,
    "took": 0.00008,
}
QUERY_TYPES_BODY = {"types": {"A": 17, "AAAA": 7, "PTR": 4, "HTTPS": 4, "OTHER": 0}, "took": 0.00009}
RECENT_BLOCKED_BODY = {"blocked": ["ad.doubleclick.net", "adservice.google.com"], "took": 0.00005}


def test_upstreams_gets_stats_upstreams_and_reads_the_servers(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(UPSTREAMS_BODY)) as api:
        upstreams = api.stats.upstreams()

    assert [(item.ip, item.port, item.count) for item in upstreams.upstreams] == [
        ("blocklist", -1, 5),
        ("cache", -1, 10),
        ("8.8.4.4", 53, 28),
    ]
    assert upstreams.upstreams[2].statistics.response == 0.016012964248657228
    assert (upstreams.forwarded_queries, upstreams.total_queries) == (28, 43)
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/stats/upstreams")


@pytest.mark.anyio
async def test_async_upstreams_gets_stats_upstreams(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(UPSTREAMS_BODY)) as api:
        upstreams = await api.stats.upstreams()

    assert upstreams.upstreams[2].name == "dns.google"
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/stats/upstreams")


def test_query_types_gets_stats_query_types(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(QUERY_TYPES_BODY)) as api:
        types = api.stats.query_types().types

    assert (types["A"], types["AAAA"]) == (17, 7)
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/stats/query_types")


@pytest.mark.anyio
async def test_async_query_types_gets_stats_query_types(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(QUERY_TYPES_BODY)) as api:
        types = (await api.stats.query_types()).types

    assert types["PTR"] == 4
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/stats/query_types")


def test_recent_blocked_asks_for_one_domain_by_default(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(RECENT_BLOCKED_BODY)) as api:
        blocked = api.stats.recent_blocked().blocked

    assert blocked == ["ad.doubleclick.net", "adservice.google.com"]
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/stats/recent_blocked")
    assert dict(request.url.params) == {"count": "1"}


@pytest.mark.anyio
async def test_async_recent_blocked_sends_count(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(RECENT_BLOCKED_BODY)) as api:
        await api.stats.recent_blocked(count=2)

    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/stats/recent_blocked")
    assert dict(request.url.params) == {"count": "2"}


# A day of the live test Pi-hole's query database.
DAY = TimeRange(start=datetime(2026, 11, 24, tzinfo=UTC), until=datetime(2026, 11, 25, tzinfo=UTC))
DAY_PARAMS = {"from": "1795478400", "until": "1795564800"}
DATABASE_SUMMARY_BODY = {
    "sum_queries": 43,
    "sum_blocked": 5,
    "percent_blocked": 11.627906799316406,
    "total_clients": 3,
    "took": 0.002,
}
DATABASE_TOP_CLIENTS_BODY = {
    "clients": [
        {"ip": "192.168.1.235", "name": "", "count": 34},
        {"ip": "127.0.0.1", "name": None, "count": 3},
        {"ip": "127.0.0.1", "name": "localhost", "count": 1},
    ],
    "total_queries": 43,
    "blocked_queries": 5,
    "took": 0.002,
}
DATABASE_UPSTREAMS_BODY = {
    "upstreams": [
        {"ip": "8.8.4.4", "name": "", "port": 53, "count": 28, "statistics": {"response": 0, "variance": 0}},
        {"ip": "cache", "name": "cache", "port": -1, "count": 10, "statistics": {"response": 0, "variance": 0}},
        {"ip": "blocklist", "name": "blocklist", "port": -1, "count": 5, "statistics": {"response": 0, "variance": 0}},
    ],
    "forwarded_queries": 28,
    "total_queries": 43,
    "took": 0.002,
}


def test_database_summary_sends_the_time_range_as_unix_seconds(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(DATABASE_SUMMARY_BODY)) as api:
        summary = api.stats.database.summary(DAY)

    assert (summary.sum_queries, summary.sum_blocked, summary.total_clients) == (43, 5, 3)
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/stats/database/summary")
    assert dict(request.url.params) == DAY_PARAMS


@pytest.mark.anyio
async def test_async_database_summary_sends_until_now_by_default(serve: Serve, sent: list[httpx2.Request]) -> None:
    start = datetime.now(UTC) - timedelta(days=1)

    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(DATABASE_SUMMARY_BODY)) as api:
        await api.stats.database.summary(TimeRange(start=start))

    [request] = sent
    assert request.url.params["from"] == str(int(start.timestamp()))
    assert abs(int(request.url.params["until"]) - datetime.now(UTC).timestamp()) < 5


def test_database_top_domains_sends_the_range_blocked_and_count(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(TOP_DOMAINS_BODY)) as api:
        top = api.stats.database.top_domains(DAY, blocked=True, count=2)

    assert top.domains[0].domain == "example.com"
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/stats/database/top_domains")
    assert dict(request.url.params) == {**DAY_PARAMS, "blocked": "true", "count": "2"}


@pytest.mark.anyio
async def test_async_database_top_clients_reads_a_client_once_per_name(
    serve: Serve, sent: list[httpx2.Request]
) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(DATABASE_TOP_CLIENTS_BODY)) as api:
        top = await api.stats.database.top_clients(DAY)

    assert [(item.ip, item.name, item.count) for item in top.clients] == [
        ("192.168.1.235", "", 34),
        ("127.0.0.1", None, 3),
        ("127.0.0.1", "localhost", 1),
    ]
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/stats/database/top_clients")
    assert dict(request.url.params) == {**DAY_PARAMS, "blocked": "false", "count": "10"}


def test_database_upstreams_reads_the_servers_then_cache_and_blocklist(
    serve: Serve, sent: list[httpx2.Request]
) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(DATABASE_UPSTREAMS_BODY)) as api:
        upstreams = api.stats.database.upstreams(DAY)

    assert [(item.ip, item.port, item.count) for item in upstreams.upstreams] == [
        ("8.8.4.4", 53, 28),
        ("cache", -1, 10),
        ("blocklist", -1, 5),
    ]
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/stats/database/upstreams")
    assert dict(request.url.params) == DAY_PARAMS


@pytest.mark.anyio
async def test_async_database_query_types_sends_the_range(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(QUERY_TYPES_BODY)) as api:
        types = (await api.stats.database.query_types(DAY)).types

    assert types["A"] == 17
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/stats/database/query_types")
    assert dict(request.url.params) == DAY_PARAMS
