import json
from collections.abc import Callable
from datetime import UTC, datetime

import httpx2
import pytest

from gravitywell import AsyncPiHole, PiHole, PiHoleAuth
from gravitywell.models import ClientKey, ClientSuggestion

BASE_URL = "http://pi.hole"
PASSWORD = "app-password"
# conftest.py's `serve` fixture.
type Serve = Callable[[object], httpx2.MockTransport]

SUBNET = "10.9.8.0/24"


def configured(client: str, comment: str | None = "gravitywell test") -> dict[str, object]:
    return {
        "client": client,
        "name": "",
        "comment": comment,
        "groups": [0],
        "id": 2,
        "date_added": 1795545266,
        "date_modified": 1795545266,
    }


# The live test Pi-hole's answers.
CLIENTS_BODY = {"clients": [configured("192.168.1.235"), configured(SUBNET, comment=None)], "took": 0.0003}
CHANGED_BODY = {
    "clients": [configured(":eth9")],
    "processed": {
        "errors": [{"item": "192.168.1.235", "error": "The item is already present"}],
        "success": [{"item": SUBNET}],
    },
    "took": 0.05,
}
SUGGESTIONS_BODY = {
    "clients": [
        {
            "hwaddr": "00:00:00:00:00:00",
            "macVendor": "virtual interface",
            "lastQuery": 1795543200,
            "addresses": "127.0.0.1,::1,0.0.0.0",
            "names": "localhost",
        },
        {"hwaddr": "0e:18:ee:8b:97:9b", "macVendor": "", "lastQuery": 0, "addresses": "172.18.0.2", "names": None},
    ],
    "took": 0.004,
}


def test_list_gets_every_client(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(CLIENTS_BODY)) as api:
        clients = api.clients.list().clients

    assert [(item.client, item.name, item.comment, item.groups) for item in clients] == [
        ("192.168.1.235", "", "gravitywell test", [0]),
        (SUBNET, "", None, [0]),
    ]
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/clients")


@pytest.mark.anyio
async def test_async_get_sends_a_subnet_as_one_path_segment(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(CLIENTS_BODY)) as api:
        await api.clients.get(SUBNET)

    [request] = sent
    assert (request.method, request.url.raw_path) == ("GET", b"/api/clients/10.9.8.0%2F24")


def test_suggestions_reads_comma_separated_addresses_and_names_as_lists(
    serve: Serve, sent: list[httpx2.Request]
) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(SUGGESTIONS_BODY)) as api:
        suggestions = api.clients.suggestions().clients

    # 0.0.0.0 is an address Pi-hole reports for the device, not a bind.
    assert [(item.addresses, item.names) for item in suggestions] == [
        (["127.0.0.1", "::1", "0.0.0.0"], ["localhost"]),  # noqa: S104
        (["172.18.0.2"], []),
    ]
    assert [item.last_query for item in suggestions] == [datetime.fromtimestamp(1795543200, tz=UTC), None]
    [request] = sent
    assert (request.method, request.url.path, dict(request.url.params)) == (
        "GET",
        "/api/clients/_suggestions",
        {"count": "50"},
    )


def test_a_client_suggestion_reads_back_the_same_from_either_dump() -> None:
    suggestion = ClientSuggestion.model_validate(SUGGESTIONS_BODY["clients"][0])

    assert ClientSuggestion.model_validate(suggestion.model_dump(mode="json")) == suggestion
    assert ClientSuggestion.model_validate(suggestion.model_dump(mode="json", by_alias=True)) == suggestion


@pytest.mark.anyio
async def test_async_add_posts_the_identifiers_and_reads_what_was_saved(
    serve: Serve, sent: list[httpx2.Request]
) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(CHANGED_BODY)) as api:
        added = await api.clients.add([SUBNET, "192.168.1.235"], comment="Living room TV", groups=[0, 2])

    assert added.processed is not None
    assert [item.item for item in added.processed.success] == [SUBNET]
    [request] = sent
    assert (request.method, request.url.path) == ("POST", "/api/clients")
    assert json.loads(request.content) == {
        "client": [SUBNET, "192.168.1.235"],
        "comment": "Living room TV",
        "groups": [0, 2],
    }


def test_update_puts_only_what_is_given(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(CHANGED_BODY)) as api:
        api.clients.update("192.168.1.235", groups=[0])

    [request] = sent
    assert (request.method, request.url.path) == ("PUT", "/api/clients/192.168.1.235")
    assert json.loads(request.content) == {"groups": [0]}


@pytest.mark.anyio
async def test_async_delete_deletes_one_client(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve({})) as api:
        await api.clients.delete(":eth9")

    [request] = sent
    assert (request.method, request.url.path) == ("DELETE", "/api/clients/:eth9")


def test_batch_delete_posts_the_clients_by_item(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve({})) as api:
        api.clients.batch.delete([ClientKey(client=":eth9"), ClientKey(client=SUBNET)])

    [request] = sent
    assert (request.method, request.url.path) == ("POST", "/api/clients:batchDelete")
    assert json.loads(request.content) == [{"item": ":eth9"}, {"item": SUBNET}]
