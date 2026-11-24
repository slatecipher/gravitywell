<h1 align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/logo-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="docs/assets/logo-light.svg">
    <img alt="gravitywell" src="https://raw.githubusercontent.com/slatecipher/gravitywell/mainline/docs/assets/logo-light.svg" width="600">
  </picture>
</h1>

<p align="center">
  <em>A typed Python client for the Pi-hole v6 REST API, with AI tools and an MCP server.</em>
</p>

<p align="center">
  <a href="https://pypi.org/project/gravitywell/"><img src="https://img.shields.io/pypi/v/gravitywell" alt="PyPI"></a>
  <a href="https://pypi.org/project/gravitywell/"><img src="https://img.shields.io/pypi/pyversions/gravitywell" alt="Python versions"></a>
  <a href="https://github.com/slatecipher/gravitywell/actions/workflows/ci.yml"><img src="https://github.com/slatecipher/gravitywell/actions/workflows/ci.yml/badge.svg?branch=mainline" alt="CI"></a>
  <a href="https://github.com/slatecipher/gravitywell/blob/mainline/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="License: MIT"></a>
</p>

## Overview

gravitywell is a Python client for [Pi-hole](https://pi-hole.net)'s v6 REST API: the blocking switch, allow and deny rules, blocklists, groups and clients, statistics and the query log, local DNS records and other settings, logs, and backups, as typed methods that return Pydantic models.

It's built for the scripts, dashboards and home automations that manage a Pi-hole, and for the AI agents that do. Each method's description is written for a model, so the same methods are tools an agent can call, marked by how much they can change, and `gravitywell-mcp` serves them to Claude and other MCP apps, read-only unless you allow more.

## Install

```bash
pip install gravitywell
```

For the MCP server, install the `mcp` extra: `pip install "gravitywell[mcp]"`.

Using an AI coding assistant? Point it at [llms.txt](https://github.com/slatecipher/gravitywell/blob/mainline/llms.txt), a compact guide to gravitywell for models.

## Quickstart

Create an application password in the Pi-hole's web interface, under **Settings › Web interface / API**, and put it in the `PIHOLE_PASSWORD` environment variable:

<!-- docs_src/readme/quickstart.py -->
```python
import os

from gravitywell import PiHole, PiHoleAuth

auth = PiHoleAuth(os.environ["PIHOLE_PASSWORD"])  # an application password

with PiHole("http://pi.hole", auth=auth) as api:
    summary = api.stats.summary()  # GET /api/stats/summary -> SummaryResponse
    print(f"{summary.queries.percent_blocked:.1f}% of queries blocked in the last 24 hours")

    status = api.dns.blocking()  # GET /api/dns/blocking -> BlockingResponse
    print(f"Blocking is {status.blocking}")  # enabled

    api.dns.set_blocking(False, timer=300)  # pause blocking for five minutes

    why = api.explain_domain("ads.example.com")  # rules, lists and recent queries in one call
    for rule in why.rules:
        print(f"{rule.type} rule ({rule.kind}): {rule.domain}")
```

- The client logs in on its first request, reuses that session, and logs out when the `with` block ends: a Pi-hole allows only a few sessions at a time.
- Each method returns a Pydantic model of the Pi-hole's answer, which your editor and type checker know field by field.
- A `4xx` or `5xx` answer raises `httpx2.HTTPStatusError`, with the Pi-hole's reason in its response.
- For async code, use `AsyncPiHole` and `await` each method, as [Async clients](https://github.com/slatecipher/gravitywell/blob/mainline/docs/async.md) explains.

## Use it from Claude

Put the Pi-hole's URL and application password in a file only you can read:

```bash
mkdir -p ~/.config/gravitywell
cat > ~/.config/gravitywell/pihole.env <<'EOF'
PIHOLE_URL=http://pi.hole
PIHOLE_PASSWORD=your-application-password
EOF
chmod 600 ~/.config/gravitywell/pihole.env
```

Then add the server to Claude Code:

```bash
claude mcp add --scope user pihole -- \
  uvx --from "gravitywell[mcp]" gravitywell-mcp --env-file ~/.config/gravitywell/pihole.env
```

Ask "is my Pi-hole healthy?", "why is this site blocked?" or "which device keeps asking for this domain?". It serves read-only tools until you add `--allow-writes` or `--allow-destructive`. [MCP server](https://github.com/slatecipher/gravitywell/blob/mainline/docs/mcp.md) covers Claude Desktop and other apps, and choosing which tools to serve.

## Features

- **The whole API.** Blocking, domain rules, lists, groups and clients, search, statistics, activity history, the query log, settings, DHCP, the network, diagnosis, logs, actions, sessions, and Teleporter backups.
- **Typed throughout.** Pydantic v2 models for every answer, `Literal` types for fixed sets of values, and times as `datetime` objects in UTC. The package type-checks in pyright's strict mode.
- **Sessions handled.** One login per client, shared by concurrent requests, renewed once when it expires, sent in a header rather than the URL, and logged out on close.
- **Sync and async.** `PiHole` and `AsyncPiHole` have the same methods, built on httpx2.
- **AI tools.** Every endpoint is also a tool for a model, with descriptions written for one, JSON Schemas, safety hints, and errors it can act on. The insights tools answer common questions in one call: why a domain is blocked, who a device is, and what's wrong with the Pi-hole.
- **An MCP server.** `gravitywell-mcp` serves the tools to Claude and other MCP apps, read-only by default, and only the areas you choose.
- **Guard rails.** It won't delete the Default group, change settings that could lock you out, hand a model the session or the password hashes, or let a misspelled setting slip past silently, as Pi-hole would.

## Guide

- [Connecting to a Pi-hole](https://github.com/slatecipher/gravitywell/blob/mainline/docs/connecting.md): the URL, application passwords, sessions, HTTPS certificates, and `app_sudo`.
- [Async clients](https://github.com/slatecipher/gravitywell/blob/mainline/docs/async.md): `AsyncPiHole`, concurrent requests and streaming.
- [Blocking and allowing](https://github.com/slatecipher/gravitywell/blob/mainline/docs/blocking.md): pausing blocking, domain rules, lists, groups and clients, and why a domain is blocked.
- [Settings](https://github.com/slatecipher/gravitywell/blob/mainline/docs/settings.md): local DNS records, upstream servers, reverse servers, static leases, and other settings.
- [Statistics and the query log](https://github.com/slatecipher/gravitywell/blob/mainline/docs/statistics.md): totals, top lists, time ranges, and the query log.
- [Health and maintenance](https://github.com/slatecipher/gravitywell/blob/mainline/docs/maintenance.md): health checks, logs, actions, the network, sessions, and backups.
- [Errors](https://github.com/slatecipher/gravitywell/blob/mainline/docs/errors.md) and [Testing](https://github.com/slatecipher/gravitywell/blob/mainline/docs/testing.md).
- [AI tools](https://github.com/slatecipher/gravitywell/blob/mainline/docs/ai-tools.md) and the [MCP server](https://github.com/slatecipher/gravitywell/blob/mainline/docs/mcp.md).
- [API reference](https://github.com/slatecipher/gravitywell/blob/mainline/docs/reference.md): every method, the endpoint it calls, and how its tool is marked.

## Compatibility

gravitywell supports Pi-hole v6, whose REST API replaced v5's interface, on Python 3.12 and newer. It was modeled on, and tested against, Pi-hole core v6.6, web v6.6.1 and FTL v6.9, which `gravitywell.PIHOLE_VERSIONS` records. [Pi-hole compatibility](https://github.com/slatecipher/gravitywell/blob/mainline/docs/compatibility.md) covers newer releases, and the few endpoints gravitywell leaves out.

## Project status

gravitywell is pre-1.0, so its API may change between minor versions. Changes are listed in the [changelog](https://github.com/slatecipher/gravitywell/blob/mainline/CHANGELOG.md). It's maintained in spare time: issues and pull requests are welcome, and [CONTRIBUTING.md](https://github.com/slatecipher/gravitywell/blob/mainline/CONTRIBUTING.md) explains how to set up and check a change.

## Acknowledgments

gravitywell is built on [ClientX](https://github.com/slatecipher/ClientX), [httpx2](https://pypi.org/project/httpx2/) and [Pydantic](https://docs.pydantic.dev), and its MCP server on [FastMCP](https://gofastmcp.com).

gravitywell is an independent, third-party project. It isn't made, endorsed or supported by the Pi-hole project, and uses the name "Pi-hole" only to say what it works with. Pi-hole® is a registered trademark of Pi-hole LLC.

## License

gravitywell is released under the [MIT License](https://github.com/slatecipher/gravitywell/blob/mainline/LICENSE).
