import json
from collections.abc import Callable
from datetime import UTC, datetime

import httpx2
import pytest

from gravitywell import AsyncPiHole, PiHole, PiHoleAuth
from gravitywell.models import ListKey

BASE_URL = "http://pi.hole"
PASSWORD = "app-password"
# conftest.py's `serve` fixture.
type Serve = Callable[[object], httpx2.MockTransport]

STEVENBLACK = "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts"
NEW = "https://example.com/gravitywell-a.txt"


def subscribed(address: str, *, date_updated: int, number: int, status: int) -> dict[str, object]:
    return {
        "address": address,
        "comment": "Migrated from /etc/pihole/adlists.list",
        "groups": [0],
        "enabled": True,
        "id": 1,
        "date_added": 1795533825,
        "date_modified": 1795533825,
        "type": "block",
        "date_updated": date_updated,
        "number": number,
        "invalid_domains": 1,
        "abp_entries": 0,
        "status": status,
    }


# The live test Pi-hole's answers.
LISTS_BODY = {
    "lists": [
        subscribed(STEVENBLACK, date_updated=1795533826, number=81677, status=1),
        subscribed(NEW, date_updated=0, number=0, status=0),
    ],
    "took": 0.0004,
}
CHANGED_BODY = {
    "lists": [subscribed(NEW, date_updated=0, number=0, status=0)],
    "processed": {
        "errors": [{"item": STEVENBLACK, "error": "The item is already present"}],
        "success": [{"item": NEW}],
    },
    "took": 0.015,
}


def test_list_gets_every_list_and_reads_a_never_updated_one_as_none(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(LISTS_BODY)) as api:
        lists = api.lists.list().lists

    assert [(item.address, item.number, item.status) for item in lists] == [(STEVENBLACK, 81677, 1), (NEW, 0, 0)]
    assert [item.date_updated for item in lists] == [datetime.fromtimestamp(1795533826, tz=UTC), None]
    [request] = sent
    assert (request.method, request.url.path, dict(request.url.params)) == ("GET", "/api/lists", {})


@pytest.mark.anyio
async def test_async_list_sends_the_type(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(LISTS_BODY)) as api:
        await api.lists.list(list_type="allow")

    [request] = sent
    assert dict(request.url.params) == {"type": "allow"}


def test_get_sends_the_url_as_one_path_segment(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(LISTS_BODY)) as api:
        api.lists.get(STEVENBLACK, list_type="block")

    [request] = sent
    assert request.method == "GET"
    assert request.url.raw_path.decode().startswith("/api/lists/https%3A%2F%2Fraw.githubusercontent.com%2F")
    assert dict(request.url.params) == {"type": "block"}


@pytest.mark.anyio
async def test_async_add_posts_the_urls_with_the_type_as_a_parameter(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(CHANGED_BODY)) as api:
        added = await api.lists.add("block", [NEW, STEVENBLACK], comment="Ads and trackers")

    assert added.processed is not None
    assert [item.item for item in added.processed.success] == [NEW]
    [request] = sent
    assert (request.method, request.url.path, dict(request.url.params)) == ("POST", "/api/lists", {"type": "block"})
    assert json.loads(request.content) == {
        "address": [NEW, STEVENBLACK],
        "comment": "Ads and trackers",
        "enabled": True,
    }


def test_update_puts_the_settings(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(CHANGED_BODY)) as api:
        api.lists.update(NEW, "block", groups=[0, 2], enabled=False)

    [request] = sent
    assert (request.method, request.url.path, dict(request.url.params)) == (
        "PUT",
        f"/api/lists/{NEW}",
        {"type": "block"},
    )
    assert json.loads(request.content) == {"groups": [0, 2], "enabled": False}


@pytest.mark.anyio
async def test_async_delete_deletes_one_list(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve({})) as api:
        await api.lists.delete(NEW, "allow")

    [request] = sent
    assert (request.method, request.url.path, dict(request.url.params)) == (
        "DELETE",
        f"/api/lists/{NEW}",
        {"type": "allow"},
    )


def test_batch_delete_posts_the_lists_by_item_and_type(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve({})) as api:
        api.lists.batch.delete([ListKey(address=NEW, type="block")])

    [request] = sent
    assert (request.method, request.url.path) == ("POST", "/api/lists:batchDelete")
    assert json.loads(request.content) == [{"item": NEW, "type": "block"}]
