# API reference

Every public name in gravitywell: the clients, the methods on each API area, the Pi-hole endpoint each one calls, what it returns, and how its AI tool is marked. Each method's docstring has the details: its arguments, limits and errors, written for a reader who sees nothing else.

## Package

| Name | What it is |
|---|---|
| `gravitywell.PiHole(base_url, *, auth, verify=True, transport=None)` | The sync client, an `httpx2.Client`. `base_url` is the Pi-hole's URL, such as `http://pi.hole`: the client sets its path to `/api`. `verify` is an `ssl.SSLContext` that trusts the Pi-hole's certificate, or `False` to skip the check. See [Connecting to a Pi-hole](connecting.md). |
| `gravitywell.AsyncPiHole(base_url, *, auth, verify=True, transport=None)` | The async client, an `httpx2.AsyncClient`, with the same areas and methods as `async def`. See [Async clients](async.md). |
| `gravitywell.PiHoleAuth(password)` | Logs in with a password, preferably an application password, or a function that returns it, called at each login, sends the session in the `X-FTL-SID` header, logs in again once after a 401, and logs out when the client closes. |
| `gravitywell.PIHOLE_VERSIONS` | The Pi-hole release gravitywell was modeled on and tested against, by component: `{"core": "v6.6", "web": "v6.6.1", "ftl": "v6.9"}`. See [Pi-hole compatibility](compatibility.md). |
| `gravitywell.__version__` | gravitywell's version, such as `0.1.0`. |
| `gravitywell.models` | The Pydantic models of request and response bodies, such as `SummaryResponse` and `TimeRange`. Each endpoint returns a model of the whole response body, and each response model has `took`, the seconds the Pi-hole took. |
| `gravitywell.mcp.create_server(api, *, areas=None, allow_writes=False, allow_destructive=False)` | Builds a FastMCP server with the AI tools of an `AsyncPiHole`, with the `mcp` extra. See [MCP server](mcp.md). |
| `gravitywell.mcp.main` | The `gravitywell-mcp` command. See [MCP server](mcp.md#options). |

Close a client to log out: leave its `with` block, or call `close()` (`await aclose()` for `AsyncPiHole`).

## Reading this reference

- **Method:** the call on a client named `api`, with its arguments and defaults, what it returns, and what it does. It returns a model from `gravitywell.models`, or `None` when the Pi-hole answers with no body. `…` stands for more optional arguments, which the [guide](README.md) and the method's docstring describe. `AsyncPiHole` has the same method, to `await`.
- **Pi-hole endpoint:** the request it sends, under the Pi-hole's `/api`. A method that checks something first, such as deleting a local DNS record, which looks up the stored entry, sends a `GET` before it.
- **AI tool:** how [`list_tools`](ai-tools.md) marks the method's tool, which decides whether [`gravitywell-mcp`](mcp.md#access-levels) serves it:
  - **read-only:** changes nothing. Served by default.
  - **write:** adds something, and deletes or overwrites nothing. Served with `--allow-writes`.
  - **destructive:** deletes, overwrites, restarts or flushes something. Served with `--allow-destructive`.
  - **not a tool:** for Python code only.

## Insights: `api`

Tools on the client itself that each answer, in one call, what takes several endpoints. A model calls them by these names; Python code can too. See [Insights tools](ai-tools.md#insights-tools).

| Method | Pi-hole endpoints | AI tool |
|---|---|---|
| `api.explain_domain(domain, recent=10)` → `DomainExplanation`<br>Explain what the Pi-hole does with a domain, and why, in one call. | `GET /api/dns/blocking`<br>`GET /api/search/{domain}`<br>`GET /api/groups`<br>`GET /api/queries` | read-only |
| `api.explain_client(address, recent=10)` → `ClientExplanation`<br>Explain who a client is, which groups it's in, and what it asked for. | `GET /api/network/devices`<br>`GET /api/clients`<br>`GET /api/groups`<br>`GET /api/queries` | read-only |
| `api.check_health()` → `HealthReport`<br>Check the Pi-hole's health in one call, and list what's wrong. | `GET /api/dns/blocking`<br>`GET /api/info/messages`<br>`GET /api/info/version`<br>`GET /api/lists`<br>`GET /api/padd` | read-only |

## Blocking: `api.dns`

Whether the Pi-hole blocks right now, and switching it, for a while or for good. See [Pausing blocking](blocking.md#pausing-blocking).

| Method | Pi-hole endpoint | AI tool |
|---|---|---|
| `api.dns.blocking()` → `BlockingResponse`<br>Fetch whether the Pi-hole is blocking ads and trackers right now. | `GET /api/dns/blocking` | read-only |
| `api.dns.set_blocking(blocking, timer=None)` → `BlockingResponse`<br>Turn the Pi-hole's blocking of ads and trackers on or off. | `POST /api/dns/blocking` | destructive |

## Domain rules: `api.domains`

Allow and deny rules for single domains (`exact`) or patterns (`regex`). See [Domain rules](blocking.md#domain-rules).

| Method | Pi-hole endpoint | AI tool |
|---|---|---|
| `api.domains.list()` → `DomainsResponse`<br>Fetch all of the Pi-hole's allow and deny rules for domains. | `GET /api/domains` | read-only |
| `api.domains.get(rule_type, rule_kind, domain)` → `DomainsResponse`<br>Fetch one allow or deny rule. | `GET /api/domains/{rule_type}/{rule_kind}/{domain}` | read-only |
| `api.domains.add(rule_type, rule_kind, domain, comment=None, groups=None, enabled=True)` → `ChangedDomainsResponse`<br>Add allow or deny rules for one or more domains. | `POST /api/domains/{rule_type}/{rule_kind}` | write |
| `api.domains.update(rule_type, rule_kind, domain, comment=None, groups=None, enabled=True)` → `ChangedDomainsResponse`<br>Change an allow or deny rule's comment, groups or state. | `PUT /api/domains/{rule_type}/{rule_kind}/{domain}` | destructive |
| `api.domains.move(domain, from_type, from_kind, to_type, to_kind, comment=None, …)` → `ChangedDomainsResponse`<br>Move an allow or deny rule to another type or kind. | `PUT /api/domains/{to_type}/{to_kind}/{domain}` | destructive |
| `api.domains.delete(rule_type, rule_kind, domain)` → `None`<br>Delete an allow or deny rule. | `DELETE /api/domains/{rule_type}/{rule_kind}/{domain}` | destructive |
| `api.domains.batch.delete(rules)` → `None`<br>Delete several allow or deny rules at once. | `POST /api/domains:batchDelete` | destructive |

## Blocklists and allowlists: `api.lists`

The blocklists and allowlists the Pi-hole subscribes to. See [Blocklists and allowlists](blocking.md#blocklists-and-allowlists).

| Method | Pi-hole endpoint | AI tool |
|---|---|---|
| `api.lists.list(list_type=None)` → `ListsResponse`<br>Fetch the blocklists and allowlists the Pi-hole subscribes to. | `GET /api/lists` | read-only |
| `api.lists.get(address, list_type=None)` → `ListsResponse`<br>Fetch one subscribed list by its URL. | `GET /api/lists/{address}` | read-only |
| `api.lists.add(list_type, address, comment=None, groups=None, enabled=True)` → `ChangedListsResponse`<br>Subscribe the Pi-hole to one or more blocklists or allowlists. | `POST /api/lists` | write |
| `api.lists.update(address, list_type, comment=None, groups=None, enabled=True)` → `ChangedListsResponse`<br>Change a subscribed list's comment, groups or state. | `PUT /api/lists/{address}` | destructive |
| `api.lists.delete(address, list_type)` → `None`<br>Unsubscribe the Pi-hole from a list. | `DELETE /api/lists/{address}` | destructive |
| `api.lists.batch.delete(lists)` → `None`<br>Unsubscribe the Pi-hole from several lists at once. | `POST /api/lists:batchDelete` | destructive |

## Groups: `api.groups`

Groups of clients, which rules and lists apply to. The Default group has ID `0`. See [Groups and clients](blocking.md#groups-and-clients).

| Method | Pi-hole endpoint | AI tool |
|---|---|---|
| `api.groups.list()` → `GroupsResponse`<br>Fetch the Pi-hole's groups of clients. | `GET /api/groups` | read-only |
| `api.groups.get(name)` → `GroupsResponse`<br>Fetch one group by its name. | `GET /api/groups/{name}` | read-only |
| `api.groups.add(name, comment=None, enabled=True)` → `ChangedGroupsResponse`<br>Add one or more groups. | `POST /api/groups` | write |
| `api.groups.update(name, comment=None, enabled=True)` → `ChangedGroupsResponse`<br>Change a group's comment or state. | `PUT /api/groups/{name}` | destructive |
| `api.groups.rename(name, new_name, comment=None, enabled=True)` → `ChangedGroupsResponse`<br>Rename a group. | `PUT /api/groups/{name}` | destructive |
| `api.groups.delete(name)` → `None`<br>Delete a group. | `DELETE /api/groups/{name}` | destructive |
| `api.groups.batch.delete(groups)` → `None`<br>Delete several groups at once. | `POST /api/groups:batchDelete` | destructive |

## Clients: `api.clients`

The devices the Pi-hole recognizes by IP address, subnet, MAC address, hostname or interface, and their groups. See [Groups and clients](blocking.md#groups-and-clients).

| Method | Pi-hole endpoint | AI tool |
|---|---|---|
| `api.clients.list()` → `ClientsResponse`<br>Fetch the clients the Pi-hole recognizes, with their groups. | `GET /api/clients` | read-only |
| `api.clients.get(client)` → `ClientsResponse`<br>Fetch one client by its identifier. | `GET /api/clients/{client}` | read-only |
| `api.clients.suggestions(count=50)` → `ClientSuggestionsResponse`<br>Fetch devices the Pi-hole has seen that aren't configured clients. | `GET /api/clients/_suggestions` | read-only |
| `api.clients.add(client, comment=None, groups=None)` → `ChangedClientsResponse`<br>Add one or more clients, to put devices into groups. | `POST /api/clients` | write |
| `api.clients.update(client, comment=None, groups=None)` → `ChangedClientsResponse`<br>Change a client's comment or groups. | `PUT /api/clients/{client}` | destructive |
| `api.clients.delete(client)` → `None`<br>Delete a client. | `DELETE /api/clients/{client}` | destructive |
| `api.clients.batch.delete(clients)` → `None`<br>Delete several clients at once. | `POST /api/clients:batchDelete` | destructive |

## Search: `api.search`

The rules and list entries that match a domain. See [Why is a domain blocked?](blocking.md#why-is-a-domain-blocked).

| Method | Pi-hole endpoint | AI tool |
|---|---|---|
| `api.search.lists(domain, partial=False, count=20)` → `SearchResponse`<br>Find the allow/deny rules and list entries that match a domain. | `GET /api/search/{domain}` | read-only |

## Statistics: `api.stats`

Totals and top lists over the last 24 hours, and, under `database`, over a time range. See [Statistics and the query log](statistics.md).

| Method | Pi-hole endpoint | AI tool |
|---|---|---|
| `api.stats.summary()` → `SummaryResponse`<br>Fetch totals of the Pi-hole's queries, clients and blocklists. | `GET /api/stats/summary` | read-only |
| `api.stats.top_domains(blocked=False, count=10)` → `TopDomainsResponse`<br>Fetch the most queried domains, permitted or blocked. | `GET /api/stats/top_domains` | read-only |
| `api.stats.top_clients(blocked=False, count=10)` → `TopClientsResponse`<br>Fetch the clients that sent the Pi-hole the most queries. | `GET /api/stats/top_clients` | read-only |
| `api.stats.upstreams()` → `UpstreamsResponse`<br>Fetch the Pi-hole's upstream DNS servers, with counts and speeds. | `GET /api/stats/upstreams` | read-only |
| `api.stats.query_types()` → `QueryTypesResponse`<br>Fetch how many queries of each DNS record type the Pi-hole got. | `GET /api/stats/query_types` | read-only |
| `api.stats.recent_blocked(count=1)` → `RecentBlockedResponse`<br>Fetch the domains the Pi-hole blocked most recently. | `GET /api/stats/recent_blocked` | read-only |
| `api.stats.database.summary(time_range)` → `DatabaseSummaryResponse`<br>Fetch totals of the Pi-hole's queries over a time range. | `GET /api/stats/database/summary` | read-only |
| `api.stats.database.top_domains(time_range, blocked=False, count=10)` → `DatabaseTopDomainsResponse`<br>Fetch the most queried domains over a time range. | `GET /api/stats/database/top_domains` | read-only |
| `api.stats.database.top_clients(time_range, blocked=False, count=10)` → `DatabaseTopClientsResponse`<br>Fetch the clients that sent the most queries over a time range. | `GET /api/stats/database/top_clients` | read-only |
| `api.stats.database.upstreams(time_range)` → `DatabaseUpstreamsResponse`<br>Fetch where the Pi-hole's queries went over a time range. | `GET /api/stats/database/upstreams` | read-only |
| `api.stats.database.query_types(time_range)` → `QueryTypesResponse`<br>Fetch the Pi-hole's queries by DNS record type over a time range. | `GET /api/stats/database/query_types` | read-only |

## Activity history: `api.history`

Query counts in 10-minute slots, over the last 24 hours or, under `database`, a time range. See [Activity over time](statistics.md#activity-over-time).

| Method | Pi-hole endpoint | AI tool |
|---|---|---|
| `api.history.activity()` → `ActivityResponse`<br>Fetch the Pi-hole's query counts over the last 24 hours. | `GET /api/history` | read-only |
| `api.history.clients(count=None)` → `ClientActivityResponse`<br>Fetch each client's query counts over the last 24 hours. | `GET /api/history/clients` | read-only |
| `api.history.database.activity(time_range)` → `DatabaseActivityResponse`<br>Fetch the Pi-hole's query counts over a time range. | `GET /api/history/database` | read-only |
| `api.history.database.clients(time_range)` → `DatabaseClientActivityResponse`<br>Fetch each client's query counts over a time range. | `GET /api/history/database/clients` | read-only |

## Query log: `api.queries`

The query log, one entry per DNS query. See [The query log](statistics.md#the-query-log).

| Method | Pi-hole endpoint | AI tool |
|---|---|---|
| `api.queries.log(time_range=None, domain=None, client_ip=None, client_name=None, …)` → `QueryLogResponse`<br>Fetch DNS queries from the Pi-hole's query log, newest first. | `GET /api/queries` | read-only |
| `api.queries.suggestions(count=30)` → `QuerySuggestionsResponse`<br>Fetch values to filter the query log by. | `GET /api/queries/suggestions` | read-only |

## Settings: `api.config`

Local DNS and CNAME records, upstream servers, reverse servers, static DHCP leases, and other settings within the topics gravitywell covers. Changes need `app_sudo` with an application password. See [Settings](settings.md).

| Method | Pi-hole endpoint | AI tool |
|---|---|---|
| `api.config.dns_records()` → `DnsRecordsResponse`<br>List the local DNS records: hostnames the Pi-hole answers itself. | `GET /api/config/dns/hosts` | read-only |
| `api.config.add_dns_record(ip, hostname)` → `None`<br>Add a local DNS record, so the Pi-hole answers `hostname` with `ip`. | `PUT /api/config/dns/hosts/{entry}` | write |
| `api.config.delete_dns_record(ip, hostname)` → `None`<br>Delete a local DNS record, so the Pi-hole stops answering `hostname`. | `DELETE /api/config/dns/hosts/{entry}` | destructive |
| `api.config.cname_records()` → `CnameRecordsResponse`<br>List the local CNAME records: aliases the Pi-hole answers itself. | `GET /api/config/dns/cnameRecords` | read-only |
| `api.config.add_cname_record(domain, target, ttl=None)` → `None`<br>Add a local CNAME record, making `domain` an alias of `target`. | `PUT /api/config/dns/cnameRecords/{entry}` | write |
| `api.config.delete_cname_record(domain, target)` → `None`<br>Delete a local CNAME record, so `domain` is no longer an alias. | `DELETE /api/config/dns/cnameRecords/{entry}` | destructive |
| `api.config.upstreams()` → `UpstreamServersResponse`<br>List the upstream DNS servers the Pi-hole forwards queries to. | `GET /api/config/dns/upstreams` | read-only |
| `api.config.set_upstreams(servers)` → `UpstreamServersResponse`<br>Replace the upstream DNS servers the Pi-hole forwards queries to. | `PATCH /api/config` | destructive |
| `api.config.settings(key)` → `ConfigSettingsResponse`<br>Read Pi-hole settings, with Pi-hole's own description of each. | `GET /api/config/{key}?detailed=true` | read-only |
| `api.config.update(changes)` → `ChangedSettingsResponse`<br>Change one or more Pi-hole settings at once, all or none. | `PATCH /api/config` | destructive |
| `api.config.reverse_servers()` → `ReverseServersResponse`<br>List the reverse servers, formerly called conditional forwarding. | `GET /api/config/dns/revServers` | read-only |
| `api.config.add_reverse_server(network, server, domain=None, enabled=True)` → `None`<br>Add a reverse server, formerly called conditional forwarding. | `PUT /api/config/dns/revServers/{entry}` | write |
| `api.config.delete_reverse_server(network, server)` → `None`<br>Delete a reverse server, formerly called conditional forwarding. | `DELETE /api/config/dns/revServers/{entry}` | destructive |
| `api.config.static_leases()` → `StaticLeasesResponse`<br>List the static DHCP leases: addresses a device always gets. | `GET /api/config/dhcp/hosts` | read-only |
| `api.config.add_static_lease(hwaddr, ip, hostname=None)` → `None`<br>Add a static DHCP lease, so a device always gets the same address. | `PUT /api/config/dhcp/hosts/{entry}` | write |
| `api.config.delete_static_lease(hwaddr)` → `None`<br>Delete a device's static DHCP lease. | `DELETE /api/config/dhcp/hosts/{entry}` | destructive |

## DHCP: `api.dhcp`

The leases of the Pi-hole's DHCP server. See [Network and DHCP](maintenance.md#network-and-dhcp).

| Method | Pi-hole endpoint | AI tool |
|---|---|---|
| `api.dhcp.leases()` → `DhcpLeasesResponse`<br>Fetch the IP addresses the Pi-hole's DHCP server has leased. | `GET /api/dhcp/leases` | read-only |
| `api.dhcp.delete_lease(ip)` → `None`<br>End a DHCP lease, freeing its IP address. | `DELETE /api/dhcp/leases/{ip}` | destructive |

## Network: `api.network`

The devices the Pi-hole has seen, and its machine's interfaces, routes and gateway. See [Network and DHCP](maintenance.md#network-and-dhcp).

| Method | Pi-hole endpoint | AI tool |
|---|---|---|
| `api.network.devices(max_devices=10, max_addresses=3)` → `NetworkDevicesResponse`<br>Fetch the devices the Pi-hole has seen on the network. | `GET /api/network/devices` | read-only |
| `api.network.delete_device(device_id)` → `None`<br>Remove a device from the Pi-hole's network table. | `DELETE /api/network/devices/{device_id}` | destructive |
| `api.network.gateway()` → `GatewayResponse`<br>Fetch the Pi-hole machine's default routes and gateways. | `GET /api/network/gateway` | read-only |
| `api.network.interfaces()` → `InterfacesResponse`<br>Fetch the Pi-hole machine's network interfaces. | `GET /api/network/interfaces` | read-only |
| `api.network.routes()` → `RoutesResponse`<br>Fetch the Pi-hole machine's routes, from every routing table. | `GET /api/network/routes` | read-only |

## Pi-hole information: `api.info`

Versions, the machine's resources and sensors, FTL's state, and the diagnosis messages. See [Health and maintenance](maintenance.md).

| Method | Pi-hole endpoint | AI tool |
|---|---|---|
| `api.info.messages()` → `MessagesResponse`<br>Fetch the problems the Pi-hole reports on its diagnosis page. | `GET /api/info/messages` | read-only |
| `api.info.message_count()` → `MessageCountResponse`<br>Fetch how many problems the Pi-hole reports. | `GET /api/info/messages/count` | read-only |
| `api.info.delete_messages(ids)` → `None`<br>Delete diagnosis messages, such as ones whose problem is fixed. | `DELETE /api/info/messages/{ids}` | destructive |
| `api.info.system()` → `SystemInfoResponse`<br>Fetch the Pi-hole machine's uptime, memory, processes and CPU use. | `GET /api/info/system` | read-only |
| `api.info.host()` → `HostInfoResponse`<br>Fetch the Pi-hole machine's operating system and hardware model. | `GET /api/info/host` | read-only |
| `api.info.sensors()` → `SensorsResponse`<br>Fetch the Pi-hole machine's hardware sensors and CPU temperature. | `GET /api/info/sensors` | read-only |
| `api.info.ftl()` → `FtlInfoResponse`<br>Fetch FTL's database contents, privacy level and resource use. | `GET /api/info/ftl` | read-only |
| `api.info.database()` → `DatabaseInfoResponse`<br>Fetch the query database's size and how many queries it holds. | `GET /api/info/database` | read-only |
| `api.info.metrics()` → `MetricsResponse`<br>Fetch FTL's DNS cache and reply counters, and its DHCP counters. | `GET /api/info/metrics` | read-only |
| `api.info.version()` → `VersionResponse`<br>Fetch the installed versions of the Pi-hole's components. | `GET /api/info/version` | read-only |

## PADD summary: `api.padd`

The Pi-hole's state in one call, as the PADD dashboard shows it. See [Health checks](maintenance.md#health-checks).

| Method | Pi-hole endpoint | AI tool |
|---|---|---|
| `api.padd.summary(full=False)` → `PaddResponse`<br>Fetch a summary of the Pi-hole's state in one call, as PADD shows it. | `GET /api/padd` | read-only |

## Logs: `api.logs`

The newest lines of the DNS resolver's, FTL's and the web server's logs, with session IDs redacted. See [Logs](maintenance.md#logs).

| Method | Pi-hole endpoint | AI tool |
|---|---|---|
| `api.logs.dnsmasq(next_id=None, lines=None)` → `LogResponse`<br>Fetch the newest lines of the DNS resolver's log, dnsmasq's. | `GET /api/logs/dnsmasq` | read-only |
| `api.logs.ftl(next_id=None, lines=None)` → `LogResponse`<br>Fetch the newest lines of FTL's log, Pi-hole's own. | `GET /api/logs/ftl` | read-only |
| `api.logs.webserver(next_id=None, lines=None)` → `LogResponse`<br>Fetch the newest lines of the web server's log. | `GET /api/logs/webserver` | read-only |

## Actions: `api.action`

Gravity updates, restarting FTL, and flushing the query log or the network table. See [Actions](maintenance.md#actions).

| Method | Pi-hole endpoint | AI tool |
|---|---|---|
| `api.action.update_gravity()` → `GravityUpdate`<br>Update gravity, downloading the lists and rebuilding their domains. | `POST /api/action/gravity` | destructive |
| `api.action.restart_dns()` → `None`<br>Restart FTL, the Pi-hole's DNS server, web server and API. | `POST /api/action/restartdns` | destructive |
| `api.action.flush_logs()` → `None`<br>Delete the last 24 hours of queries and the DNS resolver's log. | `POST /api/action/flush/logs` | destructive |
| `api.action.flush_network()` → `None`<br>Forget every device in the Pi-hole's network table. | `POST /api/action/flush/network` | destructive |

## Sessions: `api.sessions`

The sessions logged in to the API. Needs `app_sudo` with an application password. See [Sessions](maintenance.md#sessions).

| Method | Pi-hole endpoint | AI tool |
|---|---|---|
| `api.sessions.delete(session_id)` → `None`<br>Log out a session, by its number from the session list. | `DELETE /api/auth/session/{session_id}` | destructive |
| `api.sessions.list()` → `ActiveSessionsResponse`<br>List the sessions logged in to the Pi-hole's API. | `GET /api/auth/sessions` | read-only |

## Teleporter backups: `api.teleporter`

Teleporter backups, for Python code only: they hold password hashes, so they're not AI tools. Needs `app_sudo` with an application password. See [Teleporter backups](maintenance.md#teleporter-backups).

| Method | Pi-hole endpoint | AI tool |
|---|---|---|
| `api.teleporter.export()` → `Iterator[bytes]`<br>Download a Teleporter backup of the Pi-hole, as a zip archive. | `GET /api/teleporter` | not a tool |
| `api.teleporter.restore(archive, parts=None)` → `RestoreResponse`<br>Restore the Pi-hole from a Teleporter backup, replacing its contents. | `POST /api/teleporter` | not a tool |

