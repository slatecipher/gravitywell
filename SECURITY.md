# Security Policy

## Supported versions

gravitywell is pre-1.0. Security fixes go into the latest release only, so upgrade to the newest version to receive them.

## Reporting a vulnerability

**Please don't report security vulnerabilities in public issues, pull requests, or discussions.**

Report them privately through GitHub instead:

1. Go to the repository's [Security tab](https://github.com/slatecipher/gravitywell/security).
2. Click **Report a vulnerability**.
3. Describe the problem: which versions are affected, how to reproduce it, and what an attacker could do with it.

Only the maintainer can see the report. gravitywell is maintained in spare time, but security reports take priority over other work.

## What happens next

1. The maintainer confirms whether the report is a vulnerability and works on a fix, keeping you updated in the report.
2. The fix is released as a new version.
3. A GitHub security advisory is published, crediting you unless you'd rather stay anonymous.

Please keep the details private until the advisory is published.

## Scope

This policy covers gravitywell itself: its clients, its AI tools and its MCP server. Examples of what to report:

- A way for gravitywell to send or reveal a Pi-hole's password, session ID or CSRF token, such as in a URL, a log, an error or a tool's result.
- A way for an AI model to reach what gravitywell keeps from it, such as a Teleporter backup, a setting outside those `api.config` covers, or a tool `gravitywell-mcp` shouldn't serve with the options it was given.

Report vulnerabilities in Pi-hole itself to the [Pi-hole project](https://github.com/pi-hole/pi-hole/security), and those in gravitywell's dependencies, such as `clientx`, `httpx2`, `pydantic` or `fastmcp`, to those projects directly.
