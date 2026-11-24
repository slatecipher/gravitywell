import json
from collections.abc import Callable

import httpx2
import pytest
from clientx import ArgumentError
from clientx.tools import ToolError, list_tools

from gravitywell import AsyncPiHole, PiHole, PiHoleAuth
from gravitywell.models import GroupKey

BASE_URL = "http://pi.hole"
PASSWORD = "app-password"
# conftest.py's `serve` fixture.
type Serve = Callable[[object], httpx2.MockTransport]


def group(group_id: int, name: str, comment: str | None) -> dict[str, object]:
    return {
        "name": name,
        "comment": comment,
        "enabled": True,
        "id": group_id,
        "date_added": 1795544455,
        "date_modified": 1795544455,
    }


# The live test Pi-hole's answers.
GROUPS_BODY = {"groups": [group(0, "Default", "The default group"), group(5, "Kids", None)], "took": 0.0003}
CHANGED_BODY = {
    "groups": [group(5, "Kids", "test")],
    "processed": {
        "errors": [{"item": "Default", "error": "The item is already present"}],
        "success": [{"item": "Kids"}],
    },
    "took": 0.009,
}


def test_list_gets_every_group(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(GROUPS_BODY)) as api:
        groups = api.groups.list().groups

    assert [(item.id, item.name, item.comment) for item in groups] == [
        (0, "Default", "The default group"),
        (5, "Kids", None),
    ]
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/groups")


@pytest.mark.anyio
async def test_async_get_gets_one_group_by_name(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(GROUPS_BODY)) as api:
        await api.groups.get("Kids")

    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/groups/Kids")


def test_add_posts_the_names_and_reads_what_was_saved(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(CHANGED_BODY)) as api:
        added = api.groups.add(["Kids", "Default"], comment="test")

    assert added.processed is not None
    assert [(error.item, error.error) for error in added.processed.errors] == [
        ("Default", "The item is already present")
    ]
    [request] = sent
    assert (request.method, request.url.path) == ("POST", "/api/groups")
    assert json.loads(request.content) == {"name": ["Kids", "Default"], "comment": "test", "enabled": True}


@pytest.mark.anyio
async def test_async_update_puts_the_settings_without_a_name(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(CHANGED_BODY)) as api:
        await api.groups.update("Kids", enabled=False)

    [request] = sent
    assert (request.method, request.url.path) == ("PUT", "/api/groups/Kids")
    assert json.loads(request.content) == {"enabled": False}


def test_rename_puts_the_new_name_in_the_body(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(CHANGED_BODY)) as api:
        api.groups.rename("Kids", new_name="Children", comment="renamed")

    [request] = sent
    assert (request.method, request.url.path) == ("PUT", "/api/groups/Kids")
    assert json.loads(request.content) == {"name": "Children", "comment": "renamed", "enabled": True}


# Only Kids: the Default group isn't among the groups looked up.
KIDS_BODY = {"groups": [group(5, "Kids", None)], "took": 0.0003}
# The Default group, renamed: it's found by its ID, not its name.
RENAMED_DEFAULT_BODY = {"groups": [group(0, "Everyone", None)], "took": 0.0003}


@pytest.mark.anyio
async def test_async_delete_checks_the_group_then_deletes_it(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(KIDS_BODY)) as api:
        await api.groups.delete("Kids")

    assert [(request.method, request.url.path) for request in sent] == [
        ("GET", "/api/groups/Kids"),
        ("DELETE", "/api/groups/Kids"),
    ]


def test_batch_delete_checks_the_groups_then_posts_them_by_item(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(KIDS_BODY)) as api:
        api.groups.batch.delete([GroupKey(name="Kids"), GroupKey(name="Guests")])

    assert [(request.method, request.url.path) for request in sent] == [
        ("GET", "/api/groups"),
        ("POST", "/api/groups:batchDelete"),
    ]
    assert json.loads(sent[1].content) == [{"item": "Kids"}, {"item": "Guests"}]


def test_delete_checks_the_group_then_deletes_it(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(KIDS_BODY)) as api:
        api.groups.delete("Kids")

    assert [(request.method, request.url.path) for request in sent] == [
        ("GET", "/api/groups/Kids"),
        ("DELETE", "/api/groups/Kids"),
    ]


@pytest.mark.anyio
async def test_async_batch_delete_checks_the_groups_then_posts_them(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(KIDS_BODY)) as api:
        await api.groups.batch.delete([GroupKey(name="Kids")])

    assert [(request.method, request.url.path) for request in sent] == [
        ("GET", "/api/groups"),
        ("POST", "/api/groups:batchDelete"),
    ]


def test_delete_refuses_the_default_group_under_any_name(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(RENAMED_DEFAULT_BODY)) as api:
        with pytest.raises(ArgumentError, match="Refused to delete the Default group"):
            api.groups.delete("Everyone")

    assert [request.method for request in sent] == ["GET"]


@pytest.mark.anyio
async def test_async_batch_delete_refuses_if_one_group_is_the_default(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(GROUPS_BODY)) as api:
        with pytest.raises(ArgumentError, match="Refused to delete the Default group"):
            await api.groups.batch.delete([GroupKey(name="Kids"), GroupKey(name="Default")])

    assert [request.method for request in sent] == ["GET"]


def test_ai_tools_explain_the_refusal_to_a_model(serve: Serve) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(RENAMED_DEFAULT_BODY)) as api:
        tools = {tool.name: tool for tool in list_tools(api)}

        with pytest.raises(ToolError, match="disable it with an update instead"):
            tools["groups_delete"].call({"name": "Everyone"})

    assert (tools["groups_delete"].destructive, tools["groups_batch_delete"].destructive) == (True, True)
    assert not any(name.startswith("groups__") for name in tools)
