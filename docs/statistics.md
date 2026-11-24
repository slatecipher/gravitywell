# Statistics and the query log

A Pi-hole keeps the last 24 hours of queries in memory, which `api.stats`, `api.history` and `api.queries` read by default, and every query in its query database, 91 days of them by default, which their `database` variants and `disk=True` read.

## Totals and top lists

`api.stats.summary()` totals the queries, clients and blocklists. The top lists rank domains by permitted queries, or by blocked ones with `blocked=True`, and clients by all their queries:

<!-- docs_src/statistics/summary.py -->
```python
import os

from gravitywell import PiHole, PiHoleAuth

with PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
    summary = api.stats.summary()
    print(f"{summary.queries.total:,} queries, {summary.queries.percent_blocked:.1f}% blocked")
    print(f"{summary.gravity.domains_being_blocked:,} domains on the blocklists")

    for client in api.stats.top_clients(count=5).clients:
        print(f"{client.count:>6}  {client.name or client.ip}")
```

| Method | What it counts |
|---|---|
| `api.stats.summary()` | Queries: total, blocked, forwarded and cached, and by record type, status and reply. Clients, active and total. The blocklists' domains, and when gravity last updated. |
| `api.stats.top_domains(blocked=False, count=10)` | The most queried domains. |
| `api.stats.top_clients(blocked=False, count=10)` | The clients that sent the most queries. |
| `api.stats.upstreams()` | Where queries went: blocked, answered from the cache, or each upstream server, with its response times. |
| `api.stats.query_types()` | Queries by record type, such as `A`, `AAAA` and `HTTPS`. |
| `api.stats.recent_blocked(count=1)` | The most recently blocked domains, newest first, one per query. |

The Pi-hole's privacy level, `misc.privacylevel`, can hide domains or clients: the top lists are then empty, and their totals `None`. Domains and clients excluded in its settings are left out of the top lists.

## Activity over time

`api.history.activity()` counts the queries in each 10-minute slot of the last 24 hours, total, cached, blocked and forwarded: the data behind the web interface's activity graph. `api.history.clients()` counts each client's, the busiest ones by name and the rest under `others`.

## Time ranges

The `database` variants read the query database over a `TimeRange`, from `start` to `until`, which is now by default:

<!-- docs_src/statistics/time_range.py -->
```python
import os
from datetime import UTC, datetime, timedelta

from gravitywell import PiHole, PiHoleAuth
from gravitywell.models import TimeRange

last_week = TimeRange(start=datetime.now(UTC) - timedelta(days=7))  # `until` is now by default

with PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
    summary = api.stats.database.summary(last_week)
    print(f"{summary.sum_queries:,} queries last week, {summary.percent_blocked:.1f}% blocked")

    for domain in api.stats.database.top_domains(last_week, blocked=True).domains:
        print(f"{domain.count:>6}  {domain.domain}")
```

- Both times need a timezone, such as `datetime.now(UTC)` or `2026-11-24T00:00:00+01:00`: a time without one raises a `pydantic.ValidationError`, as does a `start` that isn't before `until`. gravitywell sends them as Unix seconds.
- The database gets each query within about a minute, so the last minute may be missing.
- `api.stats.database` has `summary()`, `top_domains()`, `top_clients()`, `upstreams()` and `query_types()`, and `api.history.database` has `activity()` and `clients()`.

## The query log

`api.queries.log()` returns queries, newest first, with what the Pi-hole did with each: its `status`, its `reply`, the upstream server that answered it, and the `rule_id` or `list_id` that decided it. Filters combine:

<!-- docs_src/statistics/query_log.py -->
```python
import os

from gravitywell import PiHole, PiHoleAuth

with PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
    # What did the tablet ask for that a blocklist blocked?
    page = api.queries.log(client_ip="192.168.1.50", upstream="blocklist", count=50)
    for query in page.queries:
        print(query.time, query.domain, query.status)

    # The next page skips the first 50, with the first page's cursor so new queries don't shift it.
    if page.records_filtered > 50:
        page = api.queries.log(
            client_ip="192.168.1.50", upstream="blocklist", count=50, start=50, cursor=page.cursor
        )
```

- `domain`, `client_ip`, `client_name` and `upstream` match exactly, or with `*` as a wildcard, such as `*.doubleclick.net` or `192.168.1.*`.
- `upstream="blocklist"` matches every blocked query, `"cache"` those answered from the cache, and `"permitted"` those not blocked.
- `status`, `reply`, `dnssec` and `query_type` take the values the Pi-hole uses, such as `status="GRAVITY"` for blocked by a blocklist. `api.queries.suggestions()` lists every value of each, and the domains, clients and upstream servers seen most.
- `time_range=` limits the log to a `TimeRange`, and `disk=True` reads the query database rather than the last 24 hours in memory.
- `count` queries come back at a time, 100 by default and at most 10,000. `records_filtered` says how many match. For the next page, pass `start=count`, then `2 * count` and so on, each with the first page's `cursor`, so newer queries don't shift later pages.

| `status` | What the Pi-hole did |
|---|---|
| `GRAVITY` | Blocked: on a blocklist. |
| `DENYLIST`, `REGEX` | Blocked: an exact or regex deny rule. |
| `GRAVITY_CNAME`, `DENYLIST_CNAME`, `REGEX_CNAME` | Blocked: an alias in the reply was on a blocklist or matched a deny rule. |
| `EXTERNAL_BLOCKED_IP`, `EXTERNAL_BLOCKED_NULL`, `EXTERNAL_BLOCKED_NXRA`, `EXTERNAL_BLOCKED_EDE15` | Blocked upstream: the upstream server blocked it. |
| `FORWARDED` | Answered by an upstream server. |
| `CACHE`, `CACHE_STALE` | Answered from the cache. |
| `SPECIAL_DOMAIN` | Answered by the Pi-hole itself, as a special domain. |
| `DBBUSY` | Blocked: the gravity database was busy, so the Pi-hole couldn't check its lists. |
| `RETRIED`, `RETRIED_DNSSEC`, `IN_PROGRESS`, `UNKNOWN` | Retried, still in progress, or not known. |
