import runpy
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx2
import pytest
from click.testing import CliRunner
from clientx.tools import list_tools
from fastmcp import Client, FastMCP

from gravitywell import AsyncPiHole, PiHoleAuth
from gravitywell.mcp import create_server, main

BASE_URL = "http://pi.hole"
PASSWORD = "app-password"
# conftest.py's `serve` fixture.
type Serve = Callable[[object], httpx2.MockTransport]
ENV = {"PIHOLE_URL": BASE_URL, "PIHOLE_PASSWORD": PASSWORD, "PIHOLE_VERIFY": None}


def tool_names(**options: Any) -> set[str]:
    api = AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD))
    return {
        tool.name for tool in list_tools(api) if all(getattr(tool, hint) == value for hint, value in options.items())
    }


async def served(server: FastMCP) -> dict[str, tuple[bool | None, bool | None]]:
    async with Client(server) as client:
        tools = await client.list_tools()
    return {
        tool.name: (tool.annotations.read_only_hint, tool.annotations.destructive_hint)
        for tool in tools
        if tool.annotations is not None
    }


@pytest.mark.anyio
async def test_the_server_registers_only_read_only_tools_by_default(serve: Serve) -> None:
    tools = await served(create_server(AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve({}))))

    assert set(tools) == tool_names(read_only=True)
    assert set(tools.values()) == {(True, False)}


@pytest.mark.anyio
async def test_allowing_writes_adds_those_that_destroy_nothing_and_allowing_destructive_adds_the_rest(
    serve: Serve,
) -> None:
    api = AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve({}))
    writes = await served(create_server(api, allow_writes=True))
    every = await served(create_server(api, allow_destructive=True))

    assert set(writes) == tool_names(destructive=False)
    assert set(every) == tool_names()
    assert {"config_add_dns_record", "domains_add"} <= set(writes) and "domains_delete" not in writes


@pytest.mark.anyio
async def test_areas_keep_only_their_tools(serve: Serve) -> None:
    api = AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve({}))
    tools = await served(create_server(api, areas=["dns", "padd"], allow_destructive=True))

    assert set(tools) == {"dns_blocking", "dns_set_blocking", "padd_summary"}


def test_every_tool_is_tagged_with_its_area_alone() -> None:
    # `--areas` keeps a tool by its first tag: the resource it's mounted as.
    tools = list_tools(AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD)))

    assert [(tool.name, tool.tags) for tool in tools if tool.tags != (tool.name.split("_")[0],)] == []


def test_an_unknown_area_is_refused_with_the_known_ones() -> None:
    with pytest.raises(ValueError, match=r"Unknown areas: nope\. The areas are action, clients, .*stats\."):
        create_server(AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD)), areas=["stats", "nope"])


@pytest.mark.anyio
async def test_a_tool_call_reaches_the_pi_hole_and_returns_its_model(serve: Serve, sent: list[httpx2.Request]) -> None:
    body = {"blocking": "enabled", "timer": None, "took": 0.0001}
    server = create_server(AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(body)))
    async with Client(server) as client:
        result = await client.call_tool("dns_blocking", {})

    assert result.structured_content == body
    assert [request.url.path for request in sent] == ["/api/dns/blocking"]


@pytest.mark.anyio
async def test_the_server_logs_out_when_it_stops() -> None:
    requests: list[str] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(f"{request.method} {request.url.path}")
        if request.url.path == "/api/auth":
            return httpx2.Response(200, json={"session": {"sid": "session-id"}, "took": 0.0})
        return httpx2.Response(200, json={"blocking": "enabled", "timer": None, "took": 0.0})

    api = AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=httpx2.MockTransport(handler))
    async with Client(create_server(api)) as client:
        await client.call_tool("dns_blocking", {})

    assert requests == ["POST /api/auth", "GET /api/dns/blocking", "DELETE /api/auth"]
    assert api.is_closed


@pytest.fixture
def runs(monkeypatch: pytest.MonkeyPatch) -> list[tuple[FastMCP, dict[str, Any]]]:
    """Record `FastMCP.run` calls, so the command doesn't serve."""
    calls: list[tuple[FastMCP, dict[str, Any]]] = []

    def run(self: FastMCP, **kwargs: Any) -> None:
        calls.append((self, kwargs))

    monkeypatch.setattr(FastMCP, "run", run)
    return calls


@pytest.mark.parametrize(
    ("args", "env", "message"),
    [
        # click 8.2 and later also name the environment variable.
        ([], {"PIHOLE_URL": None}, "Missing option '--url'"),
        ([], {"PIHOLE_PASSWORD": None}, "Set PIHOLE_PASSWORD to an application password"),
        (["--areas", "stats,nope"], {}, "Invalid value for --areas: Unknown areas: nope."),
        (["--verify", "/no/such/ca.pem"], {}, "Invalid value for --verify"),
    ],
)
def test_the_command_reports_what_is_missing_or_wrong(
    args: list[str], env: dict[str, str | None], message: str, runs: list[tuple[FastMCP, dict[str, Any]]]
) -> None:
    result = CliRunner().invoke(main, args, env=ENV | env)

    assert (result.exit_code, message in result.output, runs) == (2, True, [])


def test_the_command_serves_over_stdio_with_the_tools_allowed(runs: list[tuple[FastMCP, dict[str, Any]]]) -> None:
    result = CliRunner().invoke(main, ["--areas", "dns, padd", "--allow-destructive"], env=ENV)

    assert result.exit_code == 0, result.output
    [(server, kwargs)] = runs
    assert kwargs == {"transport": "stdio", "show_banner": False}
    assert server.name == "gravitywell"


@pytest.mark.parametrize(("host", "warned"), [("127.0.0.1", False), ("localhost", False), ("0.0.0.0", True)])  # noqa: S104
def test_the_command_serves_over_http_and_warns_when_others_can_reach_it(
    host: str, warned: bool, runs: list[tuple[FastMCP, dict[str, Any]]]
) -> None:
    result = CliRunner().invoke(main, ["--transport", "http", "--host", host, "--port", "8765"], env=ENV)

    assert result.exit_code == 0, result.output
    [(_, kwargs)] = runs
    assert kwargs == {"transport": "http", "host": host, "port": 8765, "show_banner": False}
    assert ("has no authentication" in result.output) is warned


@pytest.mark.parametrize(("value", "verify"), [("false", False), ("no", False), ("true", True), ("1", True)])
def test_verify_takes_true_or_false(
    value: str, verify: bool, monkeypatch: pytest.MonkeyPatch, runs: list[tuple[FastMCP, dict[str, Any]]]
) -> None:
    created: list[object] = []

    def pi_hole(url: str, **kwargs: Any) -> AsyncPiHole:
        created.append(kwargs["verify"])
        return AsyncPiHole(url, **kwargs)

    monkeypatch.setattr("gravitywell.mcp.AsyncPiHole", pi_hole)
    result = CliRunner().invoke(main, ["--verify", value], env=ENV)

    assert (result.exit_code, created) == (0, [verify])


@pytest.fixture
def created(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str]]:
    """Record the URL and password each client the command creates gets."""
    calls: list[tuple[str, str]] = []

    def pi_hole(url: str, **kwargs: Any) -> AsyncPiHole:
        calls.append(("url", url))
        return AsyncPiHole(url, **kwargs)

    def pi_hole_auth(password: str) -> PiHoleAuth:
        calls.append(("password", password))
        return PiHoleAuth(password)

    monkeypatch.setattr("gravitywell.mcp.AsyncPiHole", pi_hole)
    monkeypatch.setattr("gravitywell.mcp.PiHoleAuth", pi_hole_auth)
    return calls


def test_an_env_file_supplies_the_settings_as_written(
    tmp_path: Path, created: list[tuple[str, str]], runs: list[tuple[FastMCP, dict[str, Any]]]
) -> None:
    env_file = tmp_path / "pihole.env"
    env_file.write_text("# The test Pi-hole\nPIHOLE_URL=http://pi.hole\nPIHOLE_PASSWORD=pa${HOME}ss\n")
    unset = dict.fromkeys(ENV)

    result = CliRunner().invoke(main, ["--env-file", str(env_file)], env=unset)

    assert result.exit_code == 0, result.output
    assert sorted(created) == [("password", "pa${HOME}ss"), ("url", "http://pi.hole")]


def test_variables_already_set_win_over_the_env_file(
    tmp_path: Path, created: list[tuple[str, str]], runs: list[tuple[FastMCP, dict[str, Any]]]
) -> None:
    env_file = tmp_path / "pihole.env"
    env_file.write_text("PIHOLE_URL=http://from-the-file\nPIHOLE_PASSWORD=from-the-file\n")

    result = CliRunner().invoke(main, ["--env-file", str(env_file)], env=ENV)

    assert result.exit_code == 0, result.output
    assert sorted(created) == [("password", PASSWORD), ("url", BASE_URL)]


def test_a_missing_env_file_is_refused(tmp_path: Path, runs: list[tuple[FastMCP, dict[str, Any]]]) -> None:
    result = CliRunner().invoke(main, ["--env-file", str(tmp_path / "missing.env")], env=ENV)

    assert (result.exit_code, "does not exist" in result.output, runs) == (2, True, [])


def test_python_dash_m_runs_the_command(
    monkeypatch: pytest.MonkeyPatch, runs: list[tuple[FastMCP, dict[str, Any]]]
) -> None:
    for name, value in ENV.items():
        if value is None:
            monkeypatch.delenv(name, raising=False)
        else:
            monkeypatch.setenv(name, value)
    monkeypatch.setattr(sys, "argv", ["gravitywell.mcp", "--areas", "padd"])
    monkeypatch.delitem(sys.modules, "gravitywell.mcp")

    with pytest.raises(SystemExit) as exit_info:
        runpy.run_module("gravitywell.mcp", run_name="__main__")

    assert exit_info.value.code == 0
    assert [kwargs["transport"] for _, kwargs in runs] == ["stdio"]
