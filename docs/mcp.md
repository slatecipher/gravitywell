# MCP server

`gravitywell-mcp` serves gravitywell's [AI tools](ai-tools.md) over the [Model Context Protocol](https://modelcontextprotocol.io), so Claude Code, Claude Desktop and other MCP clients can check on and manage a Pi-hole. Ask "why is this site blocked?", "which device is making all these queries?" or "is my Pi-hole healthy?", and the model calls the tools that answer it.

It serves read-only tools unless you allow more, and only the API areas you choose.

## Install

The server is in the `mcp` extra:

```bash
pip install "gravitywell[mcp]"
```

Or let [uv](https://docs.astral.sh/uv/) run it without installing it first, as the examples below do: `uvx --from "gravitywell[mcp]" gravitywell-mcp`.

## Configure

The server reads the Pi-hole's URL and password from the environment, or from a `.env` file that `--env-file` names. The password is never an option, which would show it in process listings. Use an [application password](connecting.md#passwords), in a file only you can read:

```bash
mkdir -p ~/.config/gravitywell
cat > ~/.config/gravitywell/pihole.env <<'EOF'
PIHOLE_URL=http://pi.hole
PIHOLE_PASSWORD=your-application-password
EOF
chmod 600 ~/.config/gravitywell/pihole.env
```

| Variable | What it sets |
|---|---|
| `PIHOLE_URL` | The Pi-hole's URL, such as `http://pi.hole`. Required. |
| `PIHOLE_PASSWORD` | Its password, preferably an application password. Required. |
| `PIHOLE_VERIFY` | How to check an HTTPS certificate: `true` (the default), `false`, or the path of a CA file, such as the Pi-hole's `tls_ca.crt`. See [HTTPS](connecting.md#https). |

Variables already in the environment win over the file's, and the file's values are read as written, so a password with a `$` in it stays intact.

## Add it to an app

**Claude Code:** add it for every project with `claude mcp add`:

```bash
claude mcp add --scope user pihole -- \
  uvx --from "gravitywell[mcp]" gravitywell-mcp --env-file ~/.config/gravitywell/pihole.env
```

**Claude Desktop, or a project's `.mcp.json` in Claude Code:** add it to the `mcpServers` of the app's configuration file, which Claude Desktop opens from **Settings › Developer › Edit Config**. Give the env file's full path: `~` isn't expanded there.

```json
{
  "mcpServers": {
    "pihole": {
      "command": "uvx",
      "args": [
        "--from", "gravitywell[mcp]", "gravitywell-mcp",
        "--env-file", "/home/you/.config/gravitywell/pihole.env"
      ]
    }
  }
}
```

**Other MCP clients:** have them run `gravitywell-mcp` with the same arguments: it speaks MCP over stdio, the default. Or serve it [over HTTP](#http-transport).

Restart the app, or reconnect the server, after changing its options: the tools are chosen when it starts.

## Access levels

| Option | Tools served |
|---|---|
| None, the default | The read-only tools: they change nothing. |
| `--allow-writes` | Also the tools that only add, and delete or overwrite nothing: `domains_add`, `lists_add`, `groups_add`, `clients_add`, `config_add_dns_record`, `config_add_cname_record`, `config_add_reverse_server` and `config_add_static_lease`. |
| `--allow-destructive` | Every tool, including those that delete, update, overwrite, flush or restart, such as `domains_delete`, `dns_set_blocking`, `config_update` and `action_restart_dns`. |

Start read-only, and allow more when you need it. Most MCP clients also ask you before they run a tool. With an application password, the Pi-hole's [`app_sudo`](connecting.md#settings-that-need-app_sudo) setting is a second guard: with it off, no tool can change settings or sessions.

## Areas

`--areas` serves only the tools of the areas it names, comma-separated, such as `--areas insights,stats,queries`: fewer tools leave a model less to choose from. Every area by default.

| Area | Tools |
|---|---|
| `action` | Gravity updates, restarting FTL, flushing the query log or the network table. |
| `clients` | The clients the Pi-hole recognizes, and their groups. |
| `config` | Local DNS and CNAME records, upstream servers, reverse servers, static leases, and other settings. |
| `dhcp` | The DHCP server's leases. |
| `dns` | The blocking status, and switching it. |
| `domains` | Allow and deny rules. |
| `groups` | Groups of clients. |
| `history` | Query counts over time. |
| `info` | Versions, the machine's resources and sensors, FTL's state, diagnosis messages. |
| `insights` | `explain_domain`, `explain_client` and `check_health`, which answer in one call what takes several. |
| `lists` | Blocklists and allowlists. |
| `logs` | The DNS resolver's, FTL's and the web server's logs. |
| `network` | The devices the Pi-hole has seen, and its machine's interfaces, routes and gateway. |
| `padd` | The Pi-hole's state in one call, as PADD shows it. |
| `queries` | The query log, and values to filter it by. |
| `search` | The rules and list entries that match a domain. |
| `sessions` | The sessions logged in to the API. |
| `stats` | Totals and top lists, over the last 24 hours or a time range. |

The [API reference](reference.md) lists each area's tools.

## Options

| Option | Default | What it does |
|---|---|---|
| `--env-file FILE` | | Reads `PIHOLE_URL`, `PIHOLE_PASSWORD` and `PIHOLE_VERIFY` from a `.env` file. |
| `--url URL` | `$PIHOLE_URL` | The Pi-hole's URL. |
| `--verify VALUE` | `$PIHOLE_VERIFY`, else `true` | `true`, `false`, or a CA file to check the certificate against. |
| `--areas LIST` | every area | The [areas](#areas) to serve, comma-separated. |
| `--allow-writes` | off | Adds the tools that only add. |
| `--allow-destructive` | off | Adds every tool. Implies `--allow-writes`. |
| `--transport stdio\|http` | `stdio` | `stdio` for an app that launches the server, `http` to serve it at an address. |
| `--host HOST` | `127.0.0.1` | The HTTP transport's address. |
| `--port PORT` | `8000` | The HTTP transport's port. |

`python -m gravitywell.mcp` runs the same command.

## HTTP transport

`--transport http` serves the tools at `http://127.0.0.1:8000/mcp`, for an app that connects to a server rather than launching one:

```bash
gravitywell-mcp --env-file ~/.config/gravitywell/pihole.env --transport http
```

The HTTP transport has no authentication: anyone who can reach its address can use the Pi-hole through it, with the tools it serves. Keep it on `127.0.0.1`, the default. For any other `--host`, it prints a warning.

## How it behaves

- It logs in to the Pi-hole on the first tool call, reuses that session, and logs out when it stops.
- Its instructions tell the model what a Pi-hole is, to start with `check_health` for health and `padd_summary` for activity, to use `explain_domain` and `explain_client` for the questions they answer, and that times are in UTC.
- A tool that fails returns an error the model can read and act on, such as the setting to turn on after a `403`. Errors never include the session or the password.

## Building your own server

`gravitywell.mcp.create_server()` builds the same server from a client of your own, as a FastMCP server, so you can add tools of your own, or serve it your way:

<!-- docs_src/mcp/create_server.py -->
```python
import os

from gravitywell import AsyncPiHole, PiHoleAuth
from gravitywell.mcp import create_server

api = AsyncPiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"]))
server = create_server(api, areas=["insights", "stats", "queries", "dns"], allow_writes=True)


@server.tool
def household() -> str:
    """Describe the household network: who uses which device."""
    return "192.168.1.50 is the kids' tablet; 192.168.1.20 is the work laptop."


if __name__ == "__main__":
    server.run()  # stdio; the server logs out of the Pi-hole when it stops
```

It takes an `AsyncPiHole`, and the same choices as the command: `areas`, `allow_writes` and `allow_destructive`. An unknown area raises a `ValueError` that lists the areas. The server closes the client, logging out, when it stops.
