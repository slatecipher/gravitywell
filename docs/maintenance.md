# Health and maintenance

## Health checks

`api.check_health()` checks the Pi-hole in one call, and says what's wrong in plain words, the most urgent first:

<!-- docs_src/maintenance/health.py -->
```python
import os

from gravitywell import PiHole, PiHoleAuth

with PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
    report = api.check_health()
    for finding in report.findings:  # in plain words, the most urgent first
        print(f"- {finding}")
    if not report.findings:
        print("Nothing to fix.")
```

It reads the blocking status, the diagnosis messages, the versions, the subscribed lists and PADD's summary, and reports:

- DNS that isn't running, blocking that's off, and blocklists with no domains.
- Lists that couldn't be downloaded, and lists not downloaded yet.
- The problems the Pi-hole reports on its diagnosis page.
- A CPU at or above its temperature limit, RAM 90% used or more, and a 5-minute load at or above the CPU's cores.
- Updates available for Pi-hole's core, web interface or FTL.

Its `HealthReport` holds the details behind each finding too, such as `messages`, `updates` and `problem_lists`.

For a quick look rather than a check, `api.padd.summary()` returns the Pi-hole's state as the PADD dashboard shows it: blocking, the last 24 hours' queries, the top domain, blocked domain and client, the cache, the machine's load, memory and temperature, and key settings. `full=True` adds the network interfaces and the versions.

## Pi-hole information

| Method | What it returns |
|---|---|
| `api.info.version()` | The installed versions of core, web and FTL, and the newest release of each, as `remote`. |
| `api.info.messages()`, `message_count()` | The problems on the Pi-hole's diagnosis page, such as an invalid regex, a list that failed to download, or an unreachable upstream server. `delete_messages(ids)` deletes them once dealt with. |
| `api.info.system()` | The machine's uptime, memory, processes and CPU use. |
| `api.info.host()` | Its operating system and hardware model. |
| `api.info.sensors()` | Its hardware sensors and CPU temperature. |
| `api.info.ftl()` | FTL's database contents, privacy level and resource use. |
| `api.info.database()` | The query database's size and how many queries it holds. |
| `api.info.metrics()` | FTL's DNS cache and reply counters, and its DHCP counters. |

## Logs

`api.logs.dnsmasq()`, `ftl()` and `webserver()` return the newest lines of the DNS resolver's, FTL's and the web server's logs. The Pi-hole keeps the last 512 lines of each. `lines=` keeps only the newest few, and `next_id=` from an earlier call returns only the lines written since, to follow a log:

<!-- docs_src/maintenance/logs.py -->
```python
import os
import time

from gravitywell import PiHole, PiHoleAuth

with PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
    log = api.logs.ftl(lines=20)  # the newest 20 lines
    while True:
        for line in log.log:
            print(line.timestamp, line.prio or "", line.message)
        time.sleep(5)
        next_id = log.next_id
        log = api.logs.ftl(next_id=next_id)  # only the lines written since
        if log.next_id < next_id:  # FTL restarted, and its log started over
            log = api.logs.ftl()
```

With its `debug.api` setting on, FTL logs the session ID of each request. gravitywell replaces each one with `<redacted>`, so a log never hands a session to a script or a model.

## Actions

The actions under `api.action` each change something at once, and their AI tools are marked destructive:

| Method | What it does |
|---|---|
| `api.action.update_gravity()` | Downloads every enabled list again and rebuilds the Pi-hole's database of their domains. It waits for the update, up to 10 minutes, and returns its output and whether it `succeeded`. |
| `api.action.restart_dns()` | Restarts FTL, the Pi-hole's DNS server, web server and API: DNS and the API pause for a few seconds. Sessions survive it. |
| `api.action.flush_logs()` | Deletes the last 24 hours of queries, from memory and from the query database, and the DNS resolver's log. |
| `api.action.flush_network()` | Forgets every device in the Pi-hole's network table. |

## Network and DHCP

| Method | What it does |
|---|---|
| `api.network.devices(max_devices=10, max_addresses=3)` | The devices the Pi-hole has seen, the most recently active first, with their MAC addresses, makers, IP addresses, hostnames and query counts. |
| `api.network.delete_device(device_id)` | Removes a device from the network table. |
| `api.network.gateway()`, `interfaces()`, `routes()` | The Pi-hole machine's gateways, network interfaces and routes. |
| `api.dhcp.leases()` | The addresses the Pi-hole's DHCP server has leased. |
| `api.dhcp.delete_lease(ip)` | Ends a lease, freeing its address. |

Static leases, which give a device the same address every time, are [settings](settings.md#static-dhcp-leases).

## Sessions

`api.sessions.list()` lists the sessions logged in to the Pi-hole, by number, with when each logged in and was last active, its address and user agent, and whether it's an app, the command line, or this client (`current_session`). `delete(session_id)` logs one out, such as one an app left open:

<!-- docs_src/maintenance/sessions.py -->
```python
import os
from datetime import UTC, datetime, timedelta

from gravitywell import PiHole, PiHoleAuth

idle_since = datetime.now(UTC) - timedelta(hours=1)

with PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
    for session in api.sessions.list().sessions:
        if session.app and not session.current_session and session.last_active < idle_since:
            api.sessions.delete(session.id)  # an app's session, idle for an hour
```

Both need `app_sudo` with an application password. The list never includes session IDs, so it's safe to show.

## Teleporter backups

A Teleporter backup is a zip archive of the Pi-hole: its settings, with the local DNS records, password hashes and two-factor secret, its groups, lists, rules and clients, its DHCP leases, and its network devices and diagnosis messages. `api.teleporter.export()` streams it, so write it to a file as it comes:

<!-- docs_src/maintenance/backup.py -->
```python
import os
from pathlib import Path

from gravitywell import PiHole, PiHoleAuth

with PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
    # The archive holds password hashes: keep it as safe as a password.
    with Path("pihole-backup.zip").open("wb") as file:
        for chunk in api.teleporter.export():
            file.write(chunk)
```

`api.teleporter.restore()` restores an archive, overwriting what's there, part by part. `RestoreParts` chooses the parts, everything by default. FTL restarts afterwards. It also takes Pi-hole v5's `.tar.gz` backups:

<!-- docs_src/maintenance/restore.py -->
```python
import os
from pathlib import Path

from gravitywell import PiHole, PiHoleAuth
from gravitywell.models import GravityTables, RestoreParts

# Restore the rules, lists and groups, but keep this Pi-hole's settings, leases and clients.
tables = GravityTables(client=False, client_by_group=False)
parts = RestoreParts(config=False, dhcp_leases=False, gravity=tables)

with PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
    restored = api.teleporter.restore(Path("pihole-backup.zip").read_bytes(), parts)
    print("\n".join(restored.files))
```

Both need `app_sudo` with an application password. They aren't AI tools: a backup holds the password hashes, and a restore overwrites everything, so neither is in a model's reach.
