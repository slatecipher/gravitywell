import json
from collections.abc import Callable

import httpx2
import pytest
from clientx.tools import list_tools

from gravitywell import AsyncPiHole, PiHole, PiHoleAuth
from gravitywell.models import DomainRuleKey

BASE_URL = "http://pi.hole"
PASSWORD = "app-password"
# conftest.py's `serve` fixture.
type Serve = Callable[[object], httpx2.MockTransport]

DOMAIN = "a.gravitywell-test.example"
REGEX = r"(\.|^)example\.com$"


def rule(domain: str, rule_type: str = "deny", comment: str | None = "test") -> dict[str, object]:
    return {
        "domain": domain,
        "unicode": domain,
        "type": rule_type,
        "kind": "exact",
        "comment": comment,
        "groups": [0],
        "enabled": True,
        "id": 5,
        "date_added": 1795543652,
        "date_modified": 1795543652,
    }


# The live test Pi-hole's answers.
DOMAINS_BODY = {"domains": [rule(DOMAIN), rule("b.gravitywell-test.example", comment=None)], "took": 0.0004}
CHANGED_BODY = {
    "domains": [rule(DOMAIN)],
    "processed": {
        "errors": [{"item": DOMAIN, "error": "The item is already present"}],
        "success": [{"item": "b.gravitywell-test.example"}],
    },
    "took": 0.03,
}


def test_list_gets_every_rule(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(DOMAINS_BODY)) as api:
        rules = api.domains.list().domains

    assert [(item.domain, item.type, item.kind, item.comment, item.groups) for item in rules] == [
        (DOMAIN, "deny", "exact", "test", [0]),
        ("b.gravitywell-test.example", "deny", "exact", None, [0]),
    ]
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/domains")


@pytest.mark.anyio
async def test_async_get_gets_one_rule_by_type_kind_and_domain(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(DOMAINS_BODY)) as api:
        await api.domains.get("allow", "regex", REGEX)

    [request] = sent
    assert (request.method, request.url.path) == ("GET", f"/api/domains/allow/regex/{REGEX}")


def test_add_posts_the_domains_and_reads_what_was_saved(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(CHANGED_BODY)) as api:
        added = api.domains.add("deny", "exact", ["b.gravitywell-test.example", DOMAIN])

    assert added.processed is not None
    assert [item.item for item in added.processed.success] == ["b.gravitywell-test.example"]
    assert [(error.item, error.error) for error in added.processed.errors] == [(DOMAIN, "The item is already present")]
    [request] = sent
    assert (request.method, request.url.path) == ("POST", "/api/domains/deny/exact")
    # A comment and groups left out aren't sent: Pi-hole adds no comment and
    # the Default group.
    assert json.loads(request.content) == {"domain": ["b.gravitywell-test.example", DOMAIN], "enabled": True}


@pytest.mark.anyio
async def test_async_add_sends_a_comment_and_groups(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(CHANGED_BODY)) as api:
        await api.domains.add("allow", "regex", REGEX, comment="Breaks the banking app", groups=[0, 2], enabled=False)

    [request] = sent
    assert (request.method, request.url.path) == ("POST", "/api/domains/allow/regex")
    assert json.loads(request.content) == {
        "domain": REGEX,
        "comment": "Breaks the banking app",
        "groups": [0, 2],
        "enabled": False,
    }


def test_update_puts_the_settings_without_a_type_or_kind(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(CHANGED_BODY)) as api:
        api.domains.update("deny", "exact", DOMAIN, enabled=False)

    [request] = sent
    assert (request.method, request.url.path) == ("PUT", f"/api/domains/deny/exact/{DOMAIN}")
    assert json.loads(request.content) == {"enabled": False}


@pytest.mark.anyio
async def test_async_move_puts_to_the_new_type_and_names_the_current_one(
    serve: Serve, sent: list[httpx2.Request]
) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(CHANGED_BODY)) as api:
        await api.domains.move(
            DOMAIN, from_type="deny", from_kind="exact", to_type="allow", to_kind="exact", comment="moved"
        )

    [request] = sent
    assert (request.method, request.url.path) == ("PUT", f"/api/domains/allow/exact/{DOMAIN}")
    assert json.loads(request.content) == {"type": "deny", "kind": "exact", "comment": "moved", "enabled": True}


def test_delete_deletes_one_rule(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve({})) as api:
        api.domains.delete("allow", "regex", REGEX)

    [request] = sent
    assert (request.method, request.url.path) == ("DELETE", f"/api/domains/allow/regex/{REGEX}")


@pytest.mark.anyio
async def test_async_batch_delete_posts_the_rules_by_item_type_and_kind(
    serve: Serve, sent: list[httpx2.Request]
) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve({})) as api:
        await api.domains.batch.delete([DomainRuleKey(domain=DOMAIN, type="deny", kind="exact")])

    [request] = sent
    assert (request.method, request.url.path) == ("POST", "/api/domains:batchDelete")
    assert json.loads(request.content) == [{"item": DOMAIN, "type": "deny", "kind": "exact"}]


def test_ai_tools_mark_adding_as_safe_and_deleting_as_destructive() -> None:
    tools = {tool.name: tool for tool in list_tools(PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD)))}

    def hints(name: str) -> tuple[bool, bool, bool]:
        return (tools[name].read_only, tools[name].destructive, tools[name].idempotent)

    assert hints("domains_add") == (False, False, False)
    assert hints("domains_batch_delete") == (False, True, True)
    assert hints("domains_list") == (True, False, True)
