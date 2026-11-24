# Blocking and allowing

A Pi-hole blocks a domain by answering its DNS queries itself, so the device asking never reaches it. What it blocks comes from four places, each of which applies to groups of clients:

- **Blocklists**, which it subscribes to by URL, and **allowlists**, which exempt their domains: [`api.lists`](#blocklists-and-allowlists).
- **Allow and deny rules** that you add for single domains or for patterns: [`api.domains`](#domain-rules).
- **Groups** of **clients**, which decide whose queries each list and rule applies to: [`api.groups` and `api.clients`](#groups-and-clients).

For each query, the Pi-hole checks the lists and rules of the client's groups in this order, and stops at the first that matches:

1. An allow rule, exact or regex: allowed.
2. An exact deny rule: blocked.
3. An allowlist's domain: allowed.
4. A blocklist's domain: blocked.
5. A regex deny rule: blocked.

A domain nothing matches is allowed. [`explain_domain()`](#why-is-a-domain-blocked) shows which of them match a domain.

## Pausing blocking

`api.dns.set_blocking()` turns blocking off for every device that uses the Pi-hole, or on again. With `timer=`, the Pi-hole switches back on its own after that many seconds:

<!-- docs_src/blocking/pause.py -->
```python
import os

from gravitywell import PiHole, PiHoleAuth

with PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
    api.dns.set_blocking(False, timer=300)  # every domain gets through for five minutes

    status = api.dns.blocking()
    print(status.blocking, status.timer)  # disabled 299.9

    api.dns.set_blocking(True)  # back on now, cancelling the timer
```

`api.dns.blocking()` reads the status: `enabled`, `disabled`, `failure` when the Pi-hole's DNS server isn't running, or `unknown` while it starts. `timer` is the seconds left until a temporary change switches back, or `None`.

## Domain rules

A rule has a type, `allow` or `deny`, and a kind:

- `exact` matches one domain, such as `ads.example.com`, and not its subdomains.
- `regex` matches every domain its regular expression finds, such as `(\.|^)example\.com$` for `example.com` and all its subdomains.

`api.domains.add()` takes one domain or a list. The Pi-hole saves each one it can, and its reply's `processed` says which it saved, and why it didn't save the others, such as an invalid regex:

<!-- docs_src/blocking/rules.py -->
```python
import os

from gravitywell import PiHole, PiHoleAuth

with PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
    # Block one domain exactly, and a domain with all its subdomains by regex.
    api.domains.add("deny", "exact", "ads.example.com", comment="Banner ads")
    api.domains.add("deny", "regex", r"(\.|^)tracker\.example$")

    # Several domains at once: `processed` says which were saved, and why others weren't.
    result = api.domains.add("allow", "exact", ["cdn.example.com", "login.example.com"])
    if result.processed:
        for failure in result.processed.errors:
            print(f"{failure.item}: {failure.error}")

    for rule in api.domains.list().domains:
        print(rule.type, rule.kind, rule.domain, "enabled" if rule.enabled else "disabled")

    # Stop blocking a domain by moving its deny rule to allow, then remove the rule.
    api.domains.move(
        "ads.example.com", from_type="deny", from_kind="exact", to_type="allow", to_kind="exact"
    )
    api.domains.delete("allow", "exact", "ads.example.com")
```

- `update()` and `move()` replace a rule's settings: a `comment` left out is removed, and `enabled` left out means enabled. Groups left out stay as they are. To keep a comment, pass it again.
- `move()` changes a rule's type or kind, such as from `deny` to `allow`, and replaces its settings as `update()` does.
- `batch.delete()` deletes several rules at once, each named by a `DomainRuleKey` (`domain`, `type` and `kind`).
- Each change takes effect right away: no gravity update is needed.

## Blocklists and allowlists

`api.lists.add()` subscribes the Pi-hole to a list by its URL, as a `block` list or an `allow` list. Its domains take effect after the next gravity update, which downloads every enabled list again and rebuilds the Pi-hole's database of their domains:

<!-- docs_src/blocking/lists.py -->
```python
import os

from gravitywell import PiHole, PiHoleAuth

with PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
    api.lists.add("block", "https://example.com/hosts.txt", comment="Example blocklist")

    # A new list takes effect after a gravity update,
    # which downloads every list again and can take minutes.
    update = api.action.update_gravity()
    print("Gravity updated" if update.succeeded else update.output)

    for subscribed in api.lists.list("block").lists:
        print(f"{subscribed.number:>9,} domains  {subscribed.address}")
```

Each `SubscribedList` has `number`, its domain count, and `status`, how its last download went:

| `status` | Meaning |
|---|---|
| `0` | Not downloaded yet. |
| `1` | Downloaded. |
| `2` | Unchanged since the last download. |
| `3` | Unavailable at the last download: an older copy is in use. |
| `4` | Unavailable, with no copy: its domains aren't in effect. |

`api.action.update_gravity()` waits for the update to finish, which can take minutes, and returns its output as a terminal shows it, with `succeeded`, which Pi-hole says only inside its output. Pi-hole also updates gravity on its own once a week, by default.

## Groups and clients

Lists, rules and clients belong to groups, and a list or rule applies to the queries of the clients in its groups. Everything starts in the **Default** group, ID `0`, so a Pi-hole without groups of its own applies everything to everyone.

A client is a device, or several, identified by one of these, which the Pi-hole tries in this order:

1. Its IP address, such as `192.168.1.50`, or a subnet holding it, such as `192.168.1.0/24`.
2. Its MAC address, such as `12:34:56:78:9a:bc`.
3. Its hostname, such as `tablet.lan`.
4. The Pi-hole's network interface it uses, such as `:eth0`.

A device no client matches gets the Default group's lists and rules. To give some devices stricter rules, put them in a group of their own:

<!-- docs_src/blocking/groups.py -->
```python
import os

from gravitywell import PiHole, PiHoleAuth

with PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
    kids = api.groups.add("Kids", comment="Stricter rules").groups[0]

    # The tablet stays in the Default group (ID 0), so the usual blocking applies too.
    api.clients.add("192.168.1.50", comment="Tablet", groups=[0, kids.id])

    # A rule only the Kids group's clients get.
    api.domains.add("deny", "regex", r"(\.|^)videos\.example$", groups=[kids.id])
```

- `api.clients.suggestions()` lists the devices the Pi-hole has seen that aren't clients yet.
- `api.groups.rename()` renames a group, and `update()` changes its comment or turns it off, so its lists and rules stop applying to its clients.
- `api.groups.delete()` and `batch.delete()` refuse to delete the Default group, whatever its name, with an `ArgumentError`: Pi-hole would re-create it empty, so every list, rule and client in it would stop applying.

## Why is a domain blocked?

`api.explain_domain()` answers in one call: whether blocking is on, the rules and list entries that match the domain, the names of their groups, and the domain's most recent queries, with what the Pi-hole did with each:

<!-- docs_src/blocking/explain.py -->
```python
import os

from gravitywell import PiHole, PiHoleAuth

with PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
    why = api.explain_domain("ads.example.com")
    print(f"Blocking is {why.blocking}")
    for rule in why.rules:
        groups = ", ".join(why.groups[group] for group in rule.groups)
        print(f"{rule.type} rule ({rule.kind}) {rule.domain}, for {groups}")
    for match in why.lists:
        print(f"On the {match.type}list {match.address}")
    for query in why.recent_queries:
        print(query.time, query.client.ip, query.status)
```

- `api.search.lists()` is the search it starts from: the rules and list entries that match a domain, with `partial=True` for those that only contain it.
- `api.explain_client()` does the same for a device: the network device with that IP address, the clients that match it, best first, their groups, and its most recent queries.
- A query's `status` says what the Pi-hole did with it, such as `GRAVITY` (blocked by a blocklist), `DENYLIST` (an exact deny rule), `REGEX` (a regex deny rule), `FORWARDED` or `CACHE`. See [The query log](statistics.md#the-query-log).
