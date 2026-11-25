# Settings

`api.config` reads and changes the Pi-hole's settings: typed methods for the settings that hold lists of entries, which are easy to get wrong by hand, and `settings()` and `update()` for the rest.

With an application password, every change needs the Pi-hole's `webserver.api.app_sudo` setting on, or it answers `403`: see [Settings that need `app_sudo`](connecting.md#settings-that-need-app_sudo). Reading works without it.

Some changes restart FTL, the Pi-hole's DNS server, web server and API, to apply them, so DNS and the API pause for a second or two. The table at the end says which.

## Local DNS and CNAME records

A local DNS record makes the Pi-hole answer a hostname with an IP address itself, such as `nas.lan` for a device on your network. A CNAME record makes one name an alias of another:

<!-- docs_src/settings/local_dns.py -->
```python
import os

from gravitywell import PiHole, PiHoleAuth

with PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
    api.config.add_dns_record("192.168.1.10", "nas.lan")  # nas.lan answers 192.168.1.10
    api.config.add_cname_record("files.lan", "nas.lan")  # files.lan is an alias of nas.lan

    for record in api.config.dns_records().records:
        print(record.ip, " ".join(record.hostnames))
    for alias in api.config.cname_records().records:
        print(", ".join(alias.domains), "->", alias.target)
```

- A CNAME record's target must be a name the Pi-hole knows itself, such as a local DNS record or a DHCP client's hostname: dnsmasq doesn't follow an alias to an upstream answer. `ttl=` sets the alias's time to live, in seconds.
- `delete_dns_record()` and `delete_cname_record()` find the stored entry first, as Pi-hole deletes one only by its exact text. They refuse, with an `ArgumentError`, to delete an entry that names other hostnames or aliases too, which Pi-hole's web interface can delete whole.

## Upstream DNS servers

The Pi-hole forwards the queries it doesn't block or answer itself to its upstream servers. `api.config.upstreams()` lists them, and `set_upstreams()` replaces the list: to add a server, pass the current ones too.

```python no-check
api.config.set_upstreams(["9.9.9.9", "149.112.112.112"])  # Quad9
api.config.set_upstreams(["127.0.0.1#5335"])  # a local resolver, such as unbound, on port 5335
```

## Reverse servers

A reverse server, formerly called conditional forwarding, sends a network's reverse lookups, and its local domain's queries, to the router that hands out its addresses. The Pi-hole then shows devices' names rather than their IP addresses:

```python no-check
api.config.add_reverse_server("192.168.1.0/24", "192.168.1.1", domain="lan")
```

`reverse_servers()` lists them, and `delete_reverse_server(network, server)` deletes one.

## Static DHCP leases

When the Pi-hole is the network's DHCP server, a static lease gives a device the same IP address every time, and optionally a name:

```python no-check
api.config.add_static_lease("12:34:56:78:9a:bc", "192.168.1.50", hostname="tablet")
```

`static_leases()` lists them, and `delete_static_lease(hwaddr)` deletes a device's. A lease applies from the device's next renewal, and only while the Pi-hole's DHCP server is on (`dhcp.active`). [`api.dhcp`](maintenance.md#network-and-dhcp) shows the leases it has handed out.

## Other settings

`settings(key)` reads a topic, such as `dns`, or a single setting, such as `database.maxDBdays`, each with its value, default, allowed values, Pi-hole's own description, and `restarts_ftl`, whether changing it restarts FTL. `update(changes)` changes several at once, by dotted key, all or none:

<!-- docs_src/settings/settings.py -->
```python
import os

from gravitywell import PiHole, PiHoleAuth

with PiHole("http://pi.hole", auth=PiHoleAuth(os.environ["PIHOLE_PASSWORD"])) as api:
    [setting] = api.config.settings("database.maxDBdays").settings
    print(setting.value, setting.default, setting.description)

    # All or none: an invalid value changes nothing, and raises with Pi-hole's reason.
    api.config.update({"database.maxDBdays": 30, "dns.dnssec": True})
```

They cover the settings it's safe to hand to a script or an AI model:

| Covered | Settings |
|---|---|
| Topics | `dns`, `dhcp`, `ntp`, `resolver`, `database` and `debug` |
| Single settings | `misc.privacylevel`, and `webserver.api.excludeClients`, `excludeDomains` and `maxHistory` |

Within those, `update()` refuses `dns.port` and `dns.interface`, which could stop devices reaching the Pi-hole, and the lists that have methods of their own. Every other key raises an `ArgumentError` before anything is sent. The web server, its passwords and `app_sudo`, file paths and the rest of `misc` are out of reach on purpose: a change there could lock you out of the Pi-hole, or stop its DNS. Change them in the web interface.

- Pi-hole rejects an invalid value, or a change to a setting an environment variable sets, with a `400` that names it, and changes nothing.
- Turning the DHCP server on (`dhcp.active`) where the router serves DHCP too gives devices conflicting addresses: turn the router's off first.

## Changes that restart FTL

| Method | Restarts FTL |
|---|---|
| `add_dns_record()`, `delete_dns_record()` | No |
| `add_cname_record()`, `delete_cname_record()` | Yes |
| `set_upstreams()` | Yes |
| `add_reverse_server()`, `delete_reverse_server()` | Yes |
| `add_static_lease()`, `delete_static_lease()` | Yes |
| `update()` | Once, if a setting it changes has `restarts_ftl` |
