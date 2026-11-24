from collections.abc import Callable

import httpx2
import pytest
from clientx.tools import list_tools

from gravitywell import AsyncPiHole, PiHole, PiHoleAuth

BASE_URL = "http://pi.hole"
PASSWORD = "app-password"
# conftest.py's `serve` fixture.
type Serve = Callable[[object], httpx2.MockTransport]

# The start and end of the test Pi-hole's `pihole -g` output, as FTL sends it:
# progress lines overwritten with a carriage return and `\x1b[K`.
GRAVITY_OUTPUT = (
    "\r\x1b[K  [✓] DNS resolution is available\n"
    "\n"
    "  [i] Target: https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts\n"
    "  [i] Status: Pending...\r\x1b[K  [✓] Status: No changes detected\n"
    "\r  [✓] Parsed 81677 exact domains and 0 ABP-style domains (blocking, ignored 1 non-domain entries)\n"
    "\n"
    "  [i] Cleaning up stray matter...\r\x1b[K  [✓] Cleaning up stray matter\n"
    "\n"
    "  [✓] Done.\n"
)


def test_update_gravity_keeps_the_lines_a_terminal_would_show(serve: Serve, sent: list[httpx2.Request]) -> None:
    body = httpx2.Response(200, text=GRAVITY_OUTPUT, headers={"Content-Type": "text/plain"})
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(body)) as api:
        result = api.action.update_gravity()

    assert result.succeeded
    assert result.output == (
        "  [✓] DNS resolution is available\n"
        "\n"
        "  [i] Target: https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts\n"
        "  [✓] Status: No changes detected\n"
        "  [✓] Parsed 81677 exact domains and 0 ABP-style domains (blocking, ignored 1 non-domain entries)\n"
        "\n"
        "  [✓] Cleaning up stray matter\n"
        "\n"
        "  [✓] Done."
    )
    [request] = sent
    assert (request.method, request.url.path, dict(request.url.params)) == ("POST", "/api/action/gravity", {})


@pytest.mark.anyio
async def test_a_gravity_update_that_ends_with_gravity_failed_did_not_succeed(serve: Serve) -> None:
    text = "  [i] Target: https://example.com/list.txt\n  [✗] Status: Not found\n\nGravity failed\n"
    body = httpx2.Response(200, text=text, headers={"Content-Type": "text/plain"})
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(body)) as api:
        result = await api.action.update_gravity()

    assert (result.succeeded, result.output.split("\n")[-1]) == (False, "Gravity failed")


def test_update_gravity_waits_up_to_ten_minutes_between_chunks(serve: Serve, sent: list[httpx2.Request]) -> None:
    body = httpx2.Response(200, text="  [✓] Done.\n", headers={"Content-Type": "text/plain"})
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(body)) as api:
        api.action.update_gravity()

    [request] = sent
    assert request.extensions["timeout"] == {"connect": 10.0, "read": 600.0, "write": 10.0, "pool": 10.0}


@pytest.mark.parametrize(
    ("name", "path"),
    [
        ("restart_dns", "/api/action/restartdns"),
        ("flush_logs", "/api/action/flush/logs"),
        ("flush_network", "/api/action/flush/network"),
    ],
)
def test_each_action_posts_to_its_path(name: str, path: str, serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve({"status": "success", "took": 0.0001})) as api:
        assert getattr(api.action, name)() is None

    [request] = sent
    assert (request.method, request.url.path) == ("POST", path)


@pytest.mark.anyio
@pytest.mark.parametrize("name", ["restart_dns", "flush_logs", "flush_network"])
async def test_each_async_action_posts(name: str, serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve({"status": "success"})) as api:
        await getattr(api.action, name)()

    [request] = sent
    assert request.method == "POST"


def test_ai_tools_mark_every_action_destructive() -> None:
    # MCP's destructiveHint: false means "only additive updates", which none of
    # these is: a restart stops DNS and the API for a moment.
    tools = {tool.name: tool for tool in list_tools(PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD)))}

    def hints(name: str) -> tuple[bool, bool, bool]:
        return (tools[name].read_only, tools[name].destructive, tools[name].idempotent)

    assert (
        hints("action_restart_dns")
        == hints("action_update_gravity")
        == hints("action_flush_logs")
        == hints("action_flush_network")
        == (
            False,
            True,
            True,
        )
    )
