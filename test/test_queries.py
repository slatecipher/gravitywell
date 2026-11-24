from collections.abc import Callable
from datetime import UTC, datetime

import httpx2
import pytest

from gravitywell import AsyncPiHole, PiHole, PiHoleAuth
from gravitywell.models import LoggedQuery, TimeRange

BASE_URL = "http://pi.hole"
PASSWORD = "app-password"
# conftest.py's `serve` fixture.
type Serve = Callable[[object], httpx2.MockTransport]


def logged_query(query_id: int, list_id: int | None, ede: dict[str, object]) -> dict[str, object]:
    return {
        "id": query_id,
        "time": 1795541934.6243024,
        "type": "A",
        "status": "GRAVITY",
        "dnssec": "UNKNOWN",
        "domain": "doubleclick.net",
        "upstream": None,
        "reply": {"type": "IP", "time": 3.1e-05},
        "client": {"ip": "192.168.1.235", "name": None},
        "list_id": list_id,
        "ede": ede,
        "cname": None,
    }


NO_EDE = {"code": -1, "text": None}
# The live test Pi-hole's answer, with a rule's ID and an EDE added.
QUERY_LOG_BODY = {
    "queries": [
        logged_query(46, -3, NO_EDE),
        logged_query(45, 7, {"code": 15, "text": "Blocked"}),
        logged_query(44, None, NO_EDE),
    ],
    "cursor": 46,
    "recordsTotal": 47,
    "recordsFiltered": 6,
    "draw": 0,
    "earliest_timestamp": 1795456200,
    "earliest_timestamp_disk": 0,
    "took": 0.0004,
}
SUGGESTIONS_BODY = {
    "suggestions": {
        "domain": ["example.com", "doubleclick.net"],
        "client_ip": ["192.168.1.235"],
        "client_name": ["localhost"],
        "upstream": ["blocklist", "cache", "8.8.4.4#53 (dns.google)", "permitted"],
        "type": ["A", "AAAA"],
        "status": ["GRAVITY", "FORWARDED"],
        "reply": ["IP", "NXDOMAIN"],
        "dnssec": ["UNKNOWN", "SECURE"],
    },
    "took": 0.0001,
}


def test_log_gets_queries_with_paging_defaults(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(QUERY_LOG_BODY)) as api:
        log = api.queries.log()

    assert [query.id for query in log.queries] == [46, 45, 44]
    assert log.queries[0].time == datetime.fromtimestamp(1795541934.6243024, tz=UTC)
    assert (log.cursor, log.records_total, log.records_filtered) == (46, 47, 6)
    assert (log.earliest_timestamp, log.earliest_timestamp_disk) == (datetime.fromtimestamp(1795456200, tz=UTC), None)
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/queries")
    assert dict(request.url.params) == {"disk": "false", "length": "100", "start": "0"}


def test_a_logged_queries_list_id_splits_into_a_rule_or_list_id(serve: Serve) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(QUERY_LOG_BODY)) as api:
        queries = api.queries.log().queries

    # -3 is the subscribed list with ID 1, 7 the rule with ID 7, None neither.
    assert [(query.rule_id, query.list_id) for query in queries] == [(None, 1), (7, None), (None, None)]


def test_an_extended_dns_error_code_of_minus_one_reads_as_none(serve: Serve) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(QUERY_LOG_BODY)) as api:
        queries = api.queries.log().queries

    assert queries[0].ede is None
    assert queries[1].ede is not None
    assert (queries[1].ede.code, queries[1].ede.text) == (15, "Blocked")


@pytest.mark.anyio
async def test_async_log_sends_the_filters_and_paging(serve: Serve, sent: list[httpx2.Request]) -> None:
    day = TimeRange(start=datetime(2026, 11, 24, tzinfo=UTC), until=datetime(2026, 11, 25, tzinfo=UTC))

    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(QUERY_LOG_BODY)) as api:
        await api.queries.log(
            day,
            domain="*doubleclick*",
            client_ip="192.168.1.*",
            client_name="laptop.lan",
            upstream="blocklist",
            query_type="A",
            status="GRAVITY",
            reply="IP",
            dnssec="UNKNOWN",
            disk=True,
            count=5,
            start=5,
            cursor=46,
        )

    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/queries")
    assert dict(request.url.params) == {
        "from": "1795478400",
        "until": "1795564800",
        "domain": "*doubleclick*",
        "client_ip": "192.168.1.*",
        "client_name": "laptop.lan",
        "upstream": "blocklist",
        "type": "A",
        "status": "GRAVITY",
        "reply": "IP",
        "dnssec": "UNKNOWN",
        "disk": "true",
        "length": "5",
        "start": "5",
        "cursor": "46",
    }


def test_suggestions_gets_queries_suggestions(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(SUGGESTIONS_BODY)) as api:
        suggestions = api.queries.suggestions().suggestions

    assert suggestions.upstream == ["blocklist", "cache", "8.8.4.4#53 (dns.google)", "permitted"]
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/queries/suggestions")
    assert dict(request.url.params) == {"count": "30"}


@pytest.mark.anyio
async def test_async_suggestions_sends_count(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(SUGGESTIONS_BODY)) as api:
        await api.queries.suggestions(count=3)

    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/queries/suggestions")
    assert dict(request.url.params) == {"count": "3"}


def test_a_logged_query_reads_back_the_same_from_its_dump_or_itself(serve: Serve) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(QUERY_LOG_BODY)) as api:
        queries = api.queries.log().queries

    for query in queries:
        assert LoggedQuery.model_validate(query.model_dump(mode="json")) == query
        assert LoggedQuery.model_validate(query) == query
