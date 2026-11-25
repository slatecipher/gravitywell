# AI tools

gravitywell is written for AI models as much as for people. Each of its endpoints is also a tool a model can call, through [ClientX](https://github.com/slatecipher/ClientX/blob/mainline/docs/tools.md): `list_tools(api)` returns one per endpoint, with a description written for a model, JSON Schemas of its arguments and result, hints that say whether it changes anything, and errors a model can act on.

[`gravitywell-mcp`](mcp.md) serves these tools to Claude and other MCP clients, ready-made. This page is for using them in an agent of your own.

## Listing the tools

<!-- docs_src/ai_tools/list_tools.py -->
```python
import os

from clientx.tools import list_tools
from gravitywell import PiHole, PiHoleAuth

# Creating a client doesn't connect: the tools log in on their first call.
api = PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"]))

tools = [tool for tool in list_tools(api) if tool.read_only]
for tool in tools:
    print(f"{tool.name}: {tool.description.splitlines()[0]}")
# check_health: Check the Pi-hole's health in one call, and list what's wrong.
# stats_summary: Fetch totals of the Pi-hole's queries, clients and blocklists.
# ...
```

Creating a client doesn't connect: the tools log in on the first call. Each `Tool` has:

| Attribute | What it holds |
|---|---|
| `name` | The area and method, such as `stats_summary`, `domains_add` or `stats_database_top_domains`. The [insights tools](#insights-tools) are `explain_domain`, `explain_client` and `check_health`. |
| `description` | What the tool does, when to use it rather than a similar one, and what to expect: side effects, limits, and errors such as a `403` that needs `app_sudo`. |
| `input_schema`, `output_schema` | JSON Schemas of the arguments, each with its format, unit and allowed values, and of the result, each field described. |
| `read_only`, `destructive`, `idempotent` | Hints about what a call changes: see [Safety hints](#safety-hints). |
| `tags` | The tool's area first, such as `("stats",)`, or `("insights",)`. |
| `call(arguments)`, `acall(arguments)` | Calls the tool through the client, with the arguments the model chose. `acall()` for `AsyncPiHole`. |

## Safety hints

Each tool says how much it can change, in [MCP's terms](https://modelcontextprotocol.io/specification/2025-06-18/server/tools):

| Kind | Hints | Tools |
|---|---|---|
| Read-only | `read_only` | Every tool that only reads, such as `stats_summary`, `queries_log` and `check_health`. |
| Write | none | Tools that only add, and delete or overwrite nothing: `domains_add`, `lists_add`, `groups_add`, `clients_add`, `config_add_dns_record`, `config_add_cname_record`, `config_add_reverse_server` and `config_add_static_lease`. |
| Destructive | `destructive` | Everything else: deleting, updating, moving and renaming, `dns_set_blocking`, `config_set_upstreams` and `config_update`, and every action, such as `action_update_gravity` and `action_restart_dns`. |

A restart, a flush or an overwrite counts as destructive, though it deletes no data: MCP calls a tool non-destructive only when its update is purely additive. `idempotent` marks the tools that change nothing more when called again with the same arguments, such as setting the blocking status.

Hand a model only the tools it needs, by hint and by area:

```python no-check
areas = {"insights", "stats", "queries"}
tools = [tool for tool in list_tools(api) if tool.read_only and tool.tags[0] in areas]
```

## Insights tools

Some questions take several endpoints, and knowledge of how Pi-hole decides, to answer. The insights tools answer them in one call, as methods on the client itself, which Python code can call too:

| Tool | What it answers |
|---|---|
| `explain_domain(domain, recent=10)` | Why the Pi-hole blocks or allows a domain: whether blocking is on, the allow and deny rules and list entries that match it, the names of their groups, and its most recent queries, with what happened to each. |
| `explain_client(address, recent=10)` | Who a device is and which rules apply to it: the network device with that IP address, its maker and hostnames, the clients that match it, best first, as Pi-hole picks them, their groups, and its most recent queries. |
| `check_health()` | What's wrong with the Pi-hole, in plain words, the most urgent first: DNS or blocking off, lists that failed, diagnosis messages, temperature, memory and load, and available updates. See [Health checks](maintenance.md#health-checks). |

A model would otherwise make four or five calls for each, and need to know the order Pi-hole matches rules and clients in. `gravitywell-mcp` tells models to start with them.

## Calling tools

`tool.call(arguments)` checks the arguments, sends the request, and returns the result as JSON-ready data. A failure raises `ToolError`, whose message is for the model: each argument that's wrong and why, the reason gravitywell refused a call, or the Pi-hole's own error, with the method and path. It never includes the Pi-hole's address, the session or the password.

Each provider takes the same three fields, wrapped its own way. For Anthropic's Messages API:

<!-- docs_src/ai_tools/provider.py -->
```python
import json
import os
from typing import Any

from clientx.tools import ToolError, list_tools
from gravitywell import PiHole, PiHoleAuth

api = PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"]))
tools = {tool.name: tool for tool in list_tools(api) if tool.read_only or "dns" in tool.tags}

# Anthropic's Messages API takes these as `tools=`.
# Other providers take the same three fields, wrapped their own way.
definitions = [
    {"name": tool.name, "description": tool.description, "input_schema": tool.input_schema}
    for tool in tools.values()
]


def run_tool(name: str, arguments: dict[str, Any]) -> tuple[str, bool]:
    """Run the tool a model asked for: its result as JSON, and whether it failed."""
    try:
        return json.dumps(tools[name].call(arguments)), False
    except ToolError as error:
        return str(error), True  # what went wrong, for the model: never the session or the password


print(run_tool("dns_blocking", {}))
```

OpenAI's Responses API takes `{"type": "function", "name": ..., "description": ..., "parameters": tool.input_schema}`. ClientX's [AI tools guide](https://github.com/slatecipher/ClientX/blob/mainline/docs/tools.md) covers other formats, and serving tools with FastMCP.

## What stays out of a model's reach

gravitywell keeps the riskiest parts of the Pi-hole's API away from models, whatever tools you hand them:

- **Credentials.** It doesn't wrap `GET /api/auth`, which returns the session ID and CSRF token, or `GET /api/info/client`, which echoes the request's headers, session included. Session lists show numbers, not IDs, logs read `<redacted>` for session IDs, and tool errors never carry the session.
- **Backups.** Teleporter backups hold the password hashes, and a restore overwrites everything, so they're Python methods, not tools.
- **Settings that could lock you out.** `config_settings` and `config_update` cover the DNS, DHCP, NTP, resolver, database and debug settings and a few more, never the web server, its passwords, `app_sudo` or file paths, and `config_update` refuses changes that could stop devices reaching the Pi-hole. See [Other settings](settings.md#other-settings).
- **The Default group.** Deleting it, whatever its name, is refused: Pi-hole would re-create it empty, and every rule, list and client in it would stop applying.

The Pi-hole's `app_sudo` setting is a second guard: with an application password and `app_sudo` off, a model can't change settings, list sessions or log them out, even when it has those tools.
