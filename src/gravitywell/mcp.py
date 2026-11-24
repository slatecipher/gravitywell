"""An MCP server for gravitywell's AI tools, built on FastMCP.

Run it as `gravitywell-mcp`, or `python -m gravitywell.mcp`, with the Pi-hole's
URL and an application password in the environment, or in a `.env` file that
`--env-file` names:

    PIHOLE_URL=http://pi.hole PIHOLE_PASSWORD=... gravitywell-mcp --areas stats
    gravitywell-mcp --env-file ~/.config/gravitywell/pihole.env

It registers the read-only tools by default. `--allow-writes` adds the tools
that change something without deleting or overwriting anything, such as adding
a rule, and `--allow-destructive` adds the rest. `create_server` builds the
same server from a client of your own. It needs the `mcp` extra:
`pip install "gravitywell[mcp]"`.
"""

import ipaddress
import os
import ssl
from collections.abc import AsyncGenerator, Collection
from contextlib import asynccontextmanager

import click
from clientx.fastmcp import fastmcp_tool
from clientx.tools import Tool, list_tools
from dotenv import load_dotenv
from fastmcp import FastMCP

from gravitywell import AsyncPiHole, PiHoleAuth, __version__

__all__ = ["create_server", "main"]

_INSTRUCTIONS = """\
These tools inspect and manage a Pi-hole, the network-wide DNS sinkhole that \
blocks ads and trackers for every device that uses it as its DNS server. They \
call the Pi-hole's REST API through gravitywell, a third-party client.

- To check whether the Pi-hole is all right, start with `check_health`, and for \
its activity, `padd_summary`.
- To see why a domain is blocked or allowed, use `explain_domain`, and to \
identify a device by its IP address, `explain_client`. Each gathers several \
endpoints in one call.
- Times are in UTC. Statistics cover the last 24 hours unless a tool takes a \
time range.
- Which tools exist depends on how the server was started: read-only ones by \
default, and tools that change the Pi-hole only if the user allowed them.
"""

_HTTP_WARNING = (
    "gravitywell-mcp: warning: the HTTP transport has no authentication. Anyone who can reach {host}:{port} can use "
    "the Pi-hole with this server's tools."
)


def _allowed(tool: Tool, *, allow_writes: bool, allow_destructive: bool) -> bool:
    if tool.read_only:
        return True
    if tool.destructive:
        return allow_destructive
    return allow_writes or allow_destructive


def create_server(
    api: AsyncPiHole,
    *,
    areas: Collection[str] | None = None,
    allow_writes: bool = False,
    allow_destructive: bool = False,
) -> FastMCP:
    """Build an MCP server with `api`'s AI tools.

    It registers the read-only tools of the areas named, or of every area.
    `allow_writes` adds the tools that change something without deleting or
    overwriting anything, and `allow_destructive` adds every tool. The server
    closes `api`, logging out of its session, when it stops.

    Args:
        api: The client the tools call the Pi-hole through.
        areas: API areas, such as `stats` and `queries`: the first part of a
            tool's name, and its tag. Every area by default.
        allow_writes: Whether to add the tools that write without deleting or
            overwriting, such as adding a domain rule.
        allow_destructive: Whether to add every tool, including those that
            delete, flush, overwrite or restart.

    Raises:
        ValueError: If an area isn't one of gravitywell's.
    """
    tools = list_tools(api)
    known = sorted({tool.tags[0] for tool in tools})
    unknown = sorted(set(areas or ()) - set(known))
    if unknown:
        raise ValueError(f"Unknown areas: {', '.join(unknown)}. The areas are {', '.join(known)}.")
    chosen = [
        tool
        for tool in tools
        if (areas is None or tool.tags[0] in areas)
        and _allowed(tool, allow_writes=allow_writes, allow_destructive=allow_destructive)
    ]

    @asynccontextmanager
    async def close_client(server: FastMCP) -> AsyncGenerator[None]:
        try:
            yield
        finally:
            await api.aclose()

    return FastMCP(
        "gravitywell",
        instructions=_INSTRUCTIONS,
        version=__version__,
        tools=[fastmcp_tool(tool) for tool in chosen],
        lifespan=close_client,
    )


def _load_env_file(ctx: click.Context, param: click.Parameter, value: str | None) -> None:
    """Load a `.env` file before the options that fall back to its variables.

    Variables already in the environment win, and values are read as written,
    without `${...}` expansion, so a password with a `$` in it stays intact.
    """
    if value is not None:
        load_dotenv(value, override=False, interpolate=False)


def _areas(ctx: click.Context, param: click.Parameter, value: str | None) -> list[str] | None:
    if value is None:
        return None
    return [area.strip() for area in value.split(",") if area.strip()]


def _verify(value: str) -> ssl.SSLContext | bool:
    """Read `--verify`: `true`, `false`, or a CA file to check against."""
    if value.lower() in ("", "1", "true", "yes"):
        return True
    if value.lower() in ("0", "false", "no"):
        return False
    return ssl.create_default_context(cafile=value)


def _is_loopback(host: str) -> bool:
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return host == "localhost"


@click.command(context_settings={"help_option_names": ["-h", "--help"], "max_content_width": 100})
@click.option(
    "--env-file",
    type=click.Path(exists=True, dir_okay=False),
    callback=_load_env_file,
    is_eager=True,
    expose_value=False,
    help="A .env file to read PIHOLE_URL, PIHOLE_PASSWORD and PIHOLE_VERIFY from. Variables already set win.",
)
@click.option(
    "--url", envvar="PIHOLE_URL", show_envvar=True, required=True, help="The Pi-hole's URL, such as http://pi.hole."
)
@click.option(
    "--verify",
    envvar="PIHOLE_VERIFY",
    show_envvar=True,
    default="true",
    show_default=True,
    help="Whether to check the Pi-hole's TLS certificate: true, false, or a CA file to check it against.",
)
@click.option(
    "--areas", callback=_areas, help="Comma-separated API areas to serve, such as stats,queries,dns. All by default."
)
@click.option(
    "--allow-writes",
    is_flag=True,
    help="Add the tools that change something without deleting or overwriting, such as adding a rule.",
)
@click.option(
    "--allow-destructive",
    is_flag=True,
    help="Add every tool, including those that delete, flush, overwrite or restart. Implies --allow-writes.",
)
@click.option(
    "--transport",
    type=click.Choice(["stdio", "http"]),
    default="stdio",
    show_default=True,
    help="stdio for an app that launches the server, or http to serve it at an address.",
)
@click.option("--host", default="127.0.0.1", show_default=True, help="The HTTP transport's address.")
@click.option(
    "--port", type=click.IntRange(1, 65535), default=8000, show_default=True, help="The HTTP transport's port."
)
def main(
    url: str,
    verify: str,
    areas: list[str] | None,
    allow_writes: bool,
    allow_destructive: bool,
    transport: str,
    host: str,
    port: int,
) -> None:
    """Serve gravitywell's AI tools for a Pi-hole over MCP.

    It serves only read-only tools unless --allow-writes or --allow-destructive
    allows more. Set PIHOLE_PASSWORD to an application password, in the
    environment or a file --env-file names: it's never an option, to keep it out
    of process listings.
    """
    password = os.environ.get("PIHOLE_PASSWORD")
    if password is None:
        raise click.UsageError("Set PIHOLE_PASSWORD to an application password, or name a file with --env-file.")
    try:
        verified = _verify(verify)
    except OSError as error:
        raise click.BadParameter(str(error), param_hint="--verify") from error
    api = AsyncPiHole(url, auth=PiHoleAuth(password), verify=verified)
    try:
        server = create_server(api, areas=areas, allow_writes=allow_writes, allow_destructive=allow_destructive)
    except ValueError as error:
        raise click.BadParameter(str(error), param_hint="--areas") from error

    if transport == "stdio":
        server.run(transport="stdio", show_banner=False)
    else:
        if not _is_loopback(host):
            click.echo(_HTTP_WARNING.format(host=host, port=port), err=True)
        server.run(transport="http", host=host, port=port, show_banner=False)


if __name__ == "__main__":
    main()
