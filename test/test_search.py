from collections.abc import Callable
from datetime import UTC, datetime

import httpx2
import pytest

from gravitywell import AsyncPiHole, PiHole, PiHoleAuth

BASE_URL = "http://pi.hole"
PASSWORD = "app-password"
# conftest.py's `serve` fixture.
type Serve = Callable[[object], httpx2.MockTransport]

# The live test Pi-hole's answer for a domain with an exact deny rule, a regex
# allow rule and a blocklist entry, combined from two searches.
SEARCH_BODY = {
    "search": {
        "domains": [
            {
                "domain": "ads.gravitywell-test.example",
                "type": "deny",
                "kind": "exact",
                "comment": "gravitywell test",
                "enabled": True,
                "id": 1,
                "date_added": 1795542335,
                "date_modified": 1795542335,
                "groups": [0],
            },
            {
                "domain": "(\\.|^)gravitywell-test\\.example$",
                "type": "allow",
                "kind": "regex",
                "comment": None,
                "enabled": True,
                "id": 2,
                "date_added": 1795542336,
                "date_modified": 1795542336,
                "groups": [0],
            },
        ],
        "gravity": [
            {
                "domain": "doubleclick.net",
                "type": "block",
                "address": "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts",
                "comment": "Migrated from /etc/pihole/adlists.list",
                "enabled": True,
                "id": 1,
                "date_added": 1795533825,
                "date_modified": 1795533825,
                "date_updated": 1795533826,
                "number": 81677,
                "invalid_domains": 1,
                "abp_entries": 0,
                "status": 1,
                "groups": [0],
            }
        ],
        "results": {"domains": {"exact": 1, "regex": 1}, "gravity": {"allow": 0, "block": 1}, "total": 3},
        "parameters": {"N": 20, "partial": False, "domain": "ads.gravitywell-test.example", "debug": False},
    },
    "took": 0.0024,
}


def test_lists_gets_search_and_reads_rules_list_matches_and_counts(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(SEARCH_BODY)) as api:
        search = api.search.lists("ads.gravitywell-test.example").search

    assert [(rule.type, rule.kind, rule.domain) for rule in search.domains] == [
        ("deny", "exact", "ads.gravitywell-test.example"),
        ("allow", "regex", "(\\.|^)gravitywell-test\\.example$"),
    ]
    assert search.domains[0].date_added == datetime.fromtimestamp(1795542335, tz=UTC)
    [match] = search.gravity
    assert (match.type, match.address, match.groups) == ("block", SEARCH_BODY["search"]["gravity"][0]["address"], [0])
    assert (search.results.domains.exact, search.results.gravity.block, search.results.total) == (1, 1, 3)
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/search/ads.gravitywell-test.example")
    assert dict(request.url.params) == {"partial": "false", "N": "20"}


@pytest.mark.anyio
async def test_async_lists_sends_partial_and_count_as_n(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(SEARCH_BODY)) as api:
        await api.search.lists("doubleclick", partial=True, count=5)

    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/search/doubleclick")
    assert dict(request.url.params) == {"partial": "true", "N": "5"}
