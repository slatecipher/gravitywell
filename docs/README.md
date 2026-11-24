# gravitywell guide

One page per topic. Start with the [README](../README.md) for an overview, install and a quickstart.

## Using gravitywell

- [Connecting to a Pi-hole](connecting.md): the URL, application passwords, sessions, HTTPS certificates, and the endpoints that need `app_sudo`.
- [Async clients](async.md): `AsyncPiHole`, concurrent requests and streaming.
- [Blocking and allowing](blocking.md): how Pi-hole decides, pausing blocking, domain rules, blocklists and allowlists, groups and clients, and why a domain is blocked.
- [Settings](settings.md): local DNS and CNAME records, upstream servers, reverse servers, static DHCP leases, and other settings.
- [Statistics and the query log](statistics.md): totals and top lists, activity over time, time ranges over the query database, and filtering and paging the query log.
- [Health and maintenance](maintenance.md): health checks, Pi-hole information, logs, actions, the network and DHCP, sessions, and Teleporter backups.
- [Errors](errors.md): what gravitywell raises, and when.
- [Testing](testing.md): testing code that uses gravitywell, without a Pi-hole.

## AI

- [AI tools](ai-tools.md): gravitywell's endpoints as tools a model can call, their safety hints, the insights tools, and what stays out of a model's reach.
- [MCP server](mcp.md): `gravitywell-mcp`, for Claude Code, Claude Desktop and other MCP apps: setup, access levels and areas.

## Reference

- [API reference](reference.md): every method, the Pi-hole endpoint it calls, what it returns, and how its AI tool is marked.
- [Pi-hole compatibility](compatibility.md): the Pi-hole release gravitywell was modeled on, what it covers, and what it leaves out.
- [Changelog](../CHANGELOG.md): the changes in each release.
