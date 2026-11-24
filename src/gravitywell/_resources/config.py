"""The configuration endpoints, under `/config`.

Typed methods for the lists people change most: local DNS and CNAME records,
upstream servers, reverse servers and static DHCP leases. `settings` and
`update` read and change the other settings, within an allowlist that keeps the
password, `app_sudo`, the web server and file paths out of a model's reach.
Changing settings with an application password needs the Pi-hole's
`webserver.api.app_sudo` setting on.
"""

import ipaddress
import re
from typing import Annotated, Any, cast

from clientx import ArgumentError, AsyncResource, Json, Query, Resource, Response, Send, method
from clientx.tools import tool
from pydantic import Field, JsonValue

from gravitywell.models import (
    ChangedSettingsResponse,
    CnameRecord,
    CnameRecordsResponse,
    ConfigSetting,
    ConfigSettingsResponse,
    DnsRecord,
    DnsRecordsResponse,
    ReverseServer,
    ReverseServersResponse,
    StaticLease,
    StaticLeasesResponse,
    UpstreamServersResponse,
)

# FTL reads a `#` at an entry's start or after whitespace as a comment.
_COMMENT = re.compile(r"(?:^|\s)#.*")
# What would split an argument into several names in an entry.
_SEPARATOR = re.compile(r"[\s,#]")


def _setting(response: Response, topic: str, name: str) -> tuple[float, list[str]]:
    """Read `took` and the setting `<topic>.<name>` from a config response."""
    body: dict[str, Any] = response.json()
    return body["took"], body["config"][topic][name]


def _dns_record(entry: str) -> DnsRecord:
    ip, *hostnames = _COMMENT.sub("", entry).split()
    return DnsRecord(ip=ip, hostnames=hostnames)


def _cname_record(entry: str) -> CnameRecord:
    parts = [part.strip() for part in _COMMENT.sub("", entry).split(",")]
    ttl = int(parts.pop()) if parts[-1].isdecimal() else None
    return CnameRecord(domains=parts[:-1], target=parts[-1], ttl=ttl)


def _decode_dns_records(response: Response) -> DnsRecordsResponse:
    took, entries = _setting(response, "dns", "hosts")
    return DnsRecordsResponse(took=took, records=[_dns_record(entry) for entry in entries])


def _decode_cname_records(response: Response) -> CnameRecordsResponse:
    took, entries = _setting(response, "dns", "cnameRecords")
    return CnameRecordsResponse(took=took, records=[_cname_record(entry) for entry in entries])


def _decode_upstream_servers(response: Response) -> UpstreamServersResponse:
    took, servers = _setting(response, "dns", "upstreams")
    return UpstreamServersResponse(took=took, servers=servers)


def _decode_host_entries(response: Response) -> list[str]:
    return _setting(response, "dns", "hosts")[1]


def _decode_cname_entries(response: Response) -> list[str]:
    return _setting(response, "dns", "cnameRecords")[1]


def _check_name(value: str, parameter: str) -> None:
    if not value or _SEPARATOR.search(value):
        raise ArgumentError(
            f"`{value}` isn't a single name or address: leave out spaces, commas and `#`.", parameter=parameter
        )


def _host_entry(entries: list[str], ip: str, hostname: str) -> str:
    """Find a record's stored entry, which Pi-hole deletes by exact match."""
    for entry in entries:
        record = _dns_record(entry)
        if record.ip == ip and hostname.lower() in (name.lower() for name in record.hostnames):
            if len(record.hostnames) > 1:
                raise ArgumentError(
                    f"The record `{entry}` names other hostnames too, which deleting it would delete as well. "
                    "Pi-hole's web interface can delete the whole record.",
                    parameter="hostname",
                )
            return entry
    raise ArgumentError(
        f"No local DNS record answers `{hostname}` with `{ip}`. The DNS records endpoint lists them.",
        parameter="hostname",
    )


def _cname_entry(entries: list[str], domain: str, target: str) -> str:
    """Find a record's stored entry, whatever its TTL: Pi-hole matches it."""
    for entry in entries:
        record = _cname_record(entry)
        if domain.lower() in (alias.lower() for alias in record.domains) and record.target.lower() == target.lower():
            if len(record.domains) > 1:
                raise ArgumentError(
                    f"The record `{entry}` names other aliases too, which deleting it would delete as well. "
                    "Pi-hole's web interface can delete the whole record.",
                    parameter="domain",
                )
            return entry
    raise ArgumentError(
        f"No local CNAME record makes `{domain}` an alias of `{target}`. The CNAME records endpoint lists them.",
        parameter="domain",
    )


def _check_servers(servers: list[str]) -> None:
    if not servers:
        raise ArgumentError(
            "An empty list would leave the Pi-hole resolving only its local records: name at least one server.",
            parameter="servers",
        )


# The settings `settings` and `update` cover: these topics and keys, with
# everything under them.
_ALLOWED = (
    "dns",
    "dhcp",
    "ntp",
    "resolver",
    "database",
    "debug",
    "misc.privacylevel",
    "webserver.api.excludeClients",
    "webserver.api.excludeDomains",
    "webserver.api.maxHistory",
)
# Settings among those that `update` refuses, and why.
_REFUSED = {
    "dns.port": "moving DNS to another port would stop devices reaching the Pi-hole.",
    "dns.interface": "binding DNS to another interface could stop devices reaching the Pi-hole.",
    "dns.hosts": "the local DNS record methods change it.",
    "dns.cnameRecords": "the local CNAME record methods change it.",
    "dns.upstreams": "the upstream server methods change it.",
    "dns.revServers": "the reverse server methods change it.",
    "dhcp.hosts": "the static lease methods change it.",
}
# The fields of a setting in a detailed config, which a group of them lacks.
_SETTING_FIELDS = {"description", "allowed", "type", "value", "default", "modified", "flags"}
_MISSING = object()
_MAC = re.compile(r"^([0-9a-fA-F*]{1,2}[:-]){5}[0-9a-fA-F*]{1,2}$")
_LEASE_TIME = re.compile(r"^(\d+[smhdw]?|infinite)$")


def _under(key: str, root: str) -> bool:
    return key == root or key.startswith(f"{root}.")


def _check_key(key: str, parameter: str) -> None:
    if not any(_under(key, root) for root in _ALLOWED):
        raise ArgumentError(
            f"`{key}` is outside the settings gravitywell covers: the `dns`, `dhcp`, `ntp`, `resolver`, `database` "
            "and `debug` topics, `misc.privacylevel`, and `webserver.api.excludeClients`, `excludeDomains` and "
            "`maxHistory`.",
            parameter=parameter,
        )


def _check_changes(changes: dict[str, JsonValue]) -> None:
    if not changes:
        raise ArgumentError("Name at least one setting to change.", parameter="changes")
    for key in changes:
        _check_key(key, "changes")
        for root, reason in _REFUSED.items():
            if _under(key, root):
                raise ArgumentError(f"`{key}` can't be changed with `update`: {reason}", parameter="changes")


def _lookup(config: dict[str, Any], key: str) -> object:
    """Find a setting's value, or a group of settings, by its dotted key."""
    node: object = config
    for name in key.split("."):
        group = cast("dict[str, object]", node) if isinstance(node, dict) else None
        if group is None or name not in group:
            return _MISSING
        node = group[name]
    return node


def _check_settings_exist(config: dict[str, Any], changes: dict[str, JsonValue]) -> None:
    """Refuse keys that aren't settings, which a `PATCH` would silently skip."""
    for key in changes:
        if _lookup(config, key) is _MISSING or isinstance(_lookup(config, key), dict):
            raise ArgumentError(
                f"`{key}` isn't a setting. The settings endpoint lists them, with their keys.", parameter="changes"
            )


def _nested(changes: dict[str, JsonValue]) -> dict[str, object]:
    """Nest dotted keys as Pi-hole's config does: `dns.dnssec` in `dns`."""
    config: dict[str, object] = {}
    for key, value in changes.items():
        *groups, name = key.split(".")
        node = config
        for group in groups:
            node = cast("dict[str, object]", node.setdefault(group, {}))
        node[name] = value
    return config


def _config_settings(node: dict[str, Any], key: str) -> list[ConfigSetting]:
    """Flatten a detailed config's settings under `key`, with their keys."""
    if _SETTING_FIELDS <= node.keys():
        flags: dict[str, bool] = node["flags"]
        setting = ConfigSetting.model_validate(
            {field: node[field] for field in ("description", "type", "value", "default", "allowed", "modified")}
            | {"key": key, "restarts_ftl": flags["restart_dnsmasq"], "set_by_environment": flags["env_var"]}
        )
        return [setting]
    return [setting for name, child in node.items() for setting in _config_settings(child, f"{key}.{name}")]


def _config_settings_response(body: dict[str, Any], key: str) -> ConfigSettingsResponse:
    node = _lookup(body["config"], key)
    if not isinstance(node, dict):
        raise ArgumentError(
            f"`{key}` isn't a setting or a topic. The topics are `dns`, `dhcp`, `ntp`, `resolver`, `database` and "
            "`debug`.",
            parameter="key",
        )
    return ConfigSettingsResponse(took=body["took"], settings=_config_settings(cast("dict[str, Any]", node), key))


def _changed_settings_response(body: dict[str, Any], changes: dict[str, JsonValue]) -> ChangedSettingsResponse:
    settings = {key: _lookup(body["config"], key) for key in changes}
    return ChangedSettingsResponse.model_validate({"took": body["took"], "settings": settings})


def _reverse_server(entry: str) -> ReverseServer:
    enabled, network, server, *domain = entry.split(",")
    return ReverseServer(
        enabled=enabled == "true", network=network, server=server, domain=domain[0] if domain else None
    )


def _is_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value.strip("[]"))
    except ValueError:
        return False
    return True


def _static_lease(entry: str) -> StaticLease:
    hwaddr: str | None = None
    ip: str | None = None
    hostname: str | None = None
    lease_time: str | None = None
    for part in (part.strip() for part in entry.split(",")):
        if hwaddr is None and _MAC.match(part):
            hwaddr = part
        elif ip is None and _is_ip(part):
            ip = part.strip("[]")
        elif _LEASE_TIME.match(part):
            lease_time = part
        elif hostname is None and part not in ("", "*", "ignore") and not part.startswith(("id:", "set:", "tag:")):
            hostname = part
    return StaticLease(hwaddr=hwaddr, ip=ip, hostname=hostname, lease_time=lease_time)


def _decode_reverse_servers(response: Response) -> ReverseServersResponse:
    took, entries = _setting(response, "dns", "revServers")
    return ReverseServersResponse(took=took, servers=[_reverse_server(entry) for entry in entries])


def _decode_reverse_entries(response: Response) -> list[str]:
    return _setting(response, "dns", "revServers")[1]


def _decode_static_leases(response: Response) -> StaticLeasesResponse:
    took, entries = _setting(response, "dhcp", "hosts")
    return StaticLeasesResponse(took=took, leases=[_static_lease(entry) for entry in entries])


def _decode_lease_entries(response: Response) -> list[str]:
    return _setting(response, "dhcp", "hosts")[1]


def _check_server(value: str) -> None:
    if not value or re.search(r"[\s,]", value):
        raise ArgumentError(f"`{value}` isn't a single server: leave out spaces and commas.", parameter="server")


def _reverse_entry(entries: list[str], network: str, server: str) -> str:
    """Find a reverse server's stored entry: Pi-hole deletes by exact match."""
    for entry in entries:
        record = _reverse_server(entry)
        if record.network == network and record.server.lower() == server.lower():
            return entry
    raise ArgumentError(
        f"No reverse server forwards `{network}` to `{server}`. The reverse servers endpoint lists them.",
        parameter="network",
    )


def _lease_entry(entries: list[str], hwaddr: str) -> str:
    """Find a static lease's stored entry: Pi-hole deletes by exact match."""
    matches = [entry for entry in entries if (_static_lease(entry).hwaddr or "").lower() == hwaddr.lower()]
    if len(matches) != 1:
        found = "No static lease names" if not matches else "Several static leases name"
        raise ArgumentError(f"{found} `{hwaddr}`. The static leases endpoint lists them.", parameter="hwaddr")
    return matches[0]


class Config(Resource, prefix="/config", tags=["config"]):
    """Pi-hole settings: local DNS and CNAME records, and upstream servers."""

    # Raw requests for the methods below, which build an entry, find the stored
    # one or check the arguments first. ClientX leaves private names out of AI
    # tools.
    @method.get("/dns/hosts", decoder=_decode_host_entries)
    def _host_entries(self) -> list[str]: ...

    @method.put("/dns/hosts/{entry}")
    def _add_host(self, entry: str) -> None: ...

    @method.delete("/dns/hosts/{entry}")
    def _delete_host(self, entry: str) -> None: ...

    @method.get("/dns/cnameRecords", decoder=_decode_cname_entries)
    def _cname_entries(self) -> list[str]: ...

    @method.put("/dns/cnameRecords/{entry}")
    def _add_cname(self, entry: str) -> None: ...

    @method.delete("/dns/cnameRecords/{entry}")
    def _delete_cname(self, entry: str) -> None: ...

    @method.patch("", decoder=_decode_upstream_servers)
    def _patch_upstreams(
        self, config: Annotated[dict[str, object], Json(), Send(embed=True)]
    ) -> UpstreamServersResponse: ...

    @method.get("/dns/hosts", decoder=_decode_dns_records)
    def dns_records(self) -> DnsRecordsResponse:
        """List the local DNS records: hostnames the Pi-hole answers itself.

        Devices that use the Pi-hole resolve these names, such as `nas.lan`,
        to the IP addresses given, without asking upstream. It changes
        nothing.
        """
        ...

    @tool(idempotent=True)
    def add_dns_record(self, ip: str, hostname: str) -> None:
        """Add a local DNS record, so the Pi-hole answers `hostname` with `ip`.

        Use it to give a device on the network a name, such as `nas.lan`. It
        takes effect right away. A record that exists already answers with an
        error (400), and so does an invalid IP address or hostname.
        With an application password, it answers with an error (403) unless
        the Pi-hole's `webserver.api.app_sudo` setting is on.

        Args:
            ip: The IP address, IPv4 or IPv6, such as `192.168.1.10`.
            hostname: One hostname, such as `nas.lan`.
        """
        _check_name(ip, "ip")
        _check_name(hostname, "hostname")
        self._add_host(f"{ip} {hostname}")

    @tool(destructive=True, idempotent=True)
    def delete_dns_record(self, ip: str, hostname: str) -> None:
        """Delete a local DNS record, so the Pi-hole stops answering `hostname`.

        Devices then get an upstream answer for it, or none. It's refused if
        no record answers `hostname` with `ip`, or if the record names other
        hostnames too.
        With an application password, it answers with an error (403) unless
        the Pi-hole's `webserver.api.app_sudo` setting is on.

        Args:
            ip: The record's IP address, as `dns_records` shows it.
            hostname: The record's hostname, such as `nas.lan`.
        """
        self._delete_host(_host_entry(self._host_entries(), ip, hostname))

    @method.get("/dns/cnameRecords", decoder=_decode_cname_records)
    def cname_records(self) -> CnameRecordsResponse:
        """List the local CNAME records: aliases the Pi-hole answers itself.

        Devices that use the Pi-hole resolve each alias, such as `files.lan`,
        as its target, such as `nas.lan`. It changes nothing.
        """
        ...

    @tool(idempotent=True)
    def add_cname_record(self, domain: str, target: str, ttl: Annotated[int | None, Field(ge=0)] = None) -> None:
        """Add a local CNAME record, making `domain` an alias of `target`.

        The target must be a name the Pi-hole knows itself, such as a local
        DNS record or a DHCP client's hostname: dnsmasq doesn't follow an
        alias to an upstream answer. An alias can have only one target. FTL
        restarts to apply it, so DNS and the API pause for a second or two. A
        record that exists already answers with an error (400).
        With an application password, it answers with an error (403) unless
        the Pi-hole's `webserver.api.app_sudo` setting is on.

        Args:
            domain: The alias, such as `files.lan`.
            target: The domain it stands for, such as `nas.lan`.
            ttl: How long clients may cache the answer, in seconds. dnsmasq's
                local TTL, 0 unless set otherwise, by default.
        """
        _check_name(domain, "domain")
        _check_name(target, "target")
        entry = f"{domain},{target}" if ttl is None else f"{domain},{target},{ttl}"
        self._add_cname(entry)

    @tool(destructive=True, idempotent=True)
    def delete_cname_record(self, domain: str, target: str) -> None:
        """Delete a local CNAME record, so `domain` is no longer an alias.

        Devices then get an upstream answer for it, or none. FTL restarts to
        apply it, so DNS and the API pause for a second or two. It's refused
        if no record makes `domain` an alias of `target`, or if the record
        names other aliases too.
        With an application password, it answers with an error (403) unless
        the Pi-hole's `webserver.api.app_sudo` setting is on.

        Args:
            domain: The alias, such as `files.lan`.
            target: The domain it stands for, as `cname_records` shows it.
        """
        self._delete_cname(_cname_entry(self._cname_entries(), domain, target))

    @method.get("/dns/upstreams", decoder=_decode_upstream_servers)
    def upstreams(self) -> UpstreamServersResponse:
        """List the upstream DNS servers the Pi-hole forwards queries to.

        It forwards each query it can't answer from its cache, its local
        records or its lists. For how many queries each server answered, the
        upstreams statistics are better. It changes nothing.
        """
        ...

    @tool(destructive=True, idempotent=True)
    def set_upstreams(self, servers: Annotated[list[str], Field(min_length=1)]) -> UpstreamServersResponse:
        """Replace the upstream DNS servers the Pi-hole forwards queries to.

        Use it to switch providers, such as to Quad9's `9.9.9.9` and
        `149.112.112.112`, or to a local resolver such as `127.0.0.1#5335`.
        The list replaces the current one: to add a server, pass the current
        ones too. FTL restarts to apply it, so DNS and the API pause for a
        second or two. An invalid server answers with an error (400), and an
        empty list is refused.
        With an application password, it answers with an error (403) unless
        the Pi-hole's `webserver.api.app_sudo` setting is on.

        Args:
            servers: IP addresses or hostnames, optionally with a port after
                `#`, such as `9.9.9.9` or `127.0.0.1#5335`.
        """
        _check_servers(servers)
        return self._patch_upstreams({"dns": {"upstreams": servers}})

    @method.get("/{element}")
    def _detailed(self, element: str, detailed: Annotated[bool, Query()] = True) -> dict[str, Any]: ...

    @method.get("")
    def _config_values(self) -> dict[str, Any]: ...

    @method.patch("")
    def _patch_values(self, config: Annotated[dict[str, object], Json(), Send(embed=True)]) -> dict[str, Any]: ...

    @method.get("/dns/revServers", decoder=_decode_reverse_entries)
    def _reverse_entries(self) -> list[str]: ...

    @method.put("/dns/revServers/{entry}")
    def _add_reverse(self, entry: str) -> None: ...

    @method.delete("/dns/revServers/{entry}")
    def _delete_reverse(self, entry: str) -> None: ...

    @method.get("/dhcp/hosts", decoder=_decode_lease_entries)
    def _lease_entries(self) -> list[str]: ...

    @method.put("/dhcp/hosts/{entry}")
    def _add_lease(self, entry: str) -> None: ...

    @method.delete("/dhcp/hosts/{entry}")
    def _delete_lease(self, entry: str) -> None: ...

    @tool(read_only=True, idempotent=True)
    def settings(self, key: str) -> ConfigSettingsResponse:
        """Read Pi-hole settings, with Pi-hole's own description of each.

        Each comes with its value, default, type, allowed values, and whether
        changing it restarts FTL. Read a setting before changing it with
        `update`, for the values it allows. A topic, such as `dhcp`, returns
        all its settings, and a narrower key, such as `dns.blocking`, fewer:
        `dns` has 45. It covers the `dns`, `dhcp`, `ntp`, `resolver`,
        `database` and `debug` topics, `misc.privacylevel`, and
        `webserver.api.excludeClients`, `excludeDomains` and `maxHistory`, and
        refuses other keys. It changes nothing.

        Args:
            key: A topic or a dotted key, such as `dhcp`, `dns.blocking` or
                `dns.dnssec`.
        """
        _check_key(key, "key")
        return _config_settings_response(self._detailed(key.replace(".", "/")), key)

    @tool(destructive=True, idempotent=True)
    def update(self, changes: Annotated[dict[str, JsonValue], Field(min_length=1)]) -> ChangedSettingsResponse:
        """Change one or more Pi-hole settings at once, all or none.

        Read them with `settings` first, for the values they allow. Pi-hole
        answers an invalid value, or a change to a setting an environment
        variable sets, with an error (400) that names it, and then changes
        nothing. If a changed setting's `restarts_ftl` is true, FTL
        restarts once, so DNS and the API pause for a second or two. It covers
        the settings `settings` reads, except `dns.port` and `dns.interface`,
        which could stop devices reaching the Pi-hole, and the lists with
        methods of their own: local DNS and CNAME records, upstreams, reverse
        servers and static leases. Turning the DHCP server on (`dhcp.active`)
        where the router serves DHCP too gives devices conflicting addresses:
        turn the router's off first.
        With an application password, it answers with an error (403) unless
        the Pi-hole's `webserver.api.app_sudo` setting is on.

        Args:
            changes: The new values by dotted key, such as
                `{"dns.dnssec": true, "misc.privacylevel": 1}`.
        """
        _check_changes(changes)
        _check_settings_exist(self._config_values()["config"], changes)
        return _changed_settings_response(self._patch_values(_nested(changes)), changes)

    @method.get("/dns/revServers", decoder=_decode_reverse_servers)
    def reverse_servers(self) -> ReverseServersResponse:
        """List the reverse servers, formerly called conditional forwarding.

        Each sends the reverse lookups of a network's addresses, and the
        queries for its local domain, to a server that knows the devices'
        names, usually the router, so the statistics show names rather than
        IP addresses. It changes nothing.
        """
        ...

    @tool(idempotent=True)
    def add_reverse_server(self, network: str, server: str, domain: str | None = None, enabled: bool = True) -> None:
        """Add a reverse server, formerly called conditional forwarding.

        Use it so the Pi-hole learns the names of a network's devices from the
        router that gives out their addresses: it forwards the network's
        reverse lookups, and its local domain's queries, there. FTL restarts
        to apply it, so DNS and the API pause for a second or two. Pi-hole
        answers an invalid network or server with an error (400), and an
        existing reverse server too.
        With an application password, it answers with an error (403) unless
        the Pi-hole's `webserver.api.app_sudo` setting is on.

        Args:
            network: The network in CIDR notation, such as `192.168.1.0/24`.
                Without a prefix length, it's that one address only.
            server: The server to forward to, usually the router, such as
                `192.168.1.1`, optionally with a port after `#`.
            domain: The network's local domain, such as `lan` or `fritz.box`,
                whose queries go there too.
            enabled: Whether it's in effect right away.
        """
        _check_name(network, "network")
        _check_server(server)
        if domain is not None:
            _check_name(domain, "domain")
        parts = ["true" if enabled else "false", network, server, *([domain] if domain else [])]
        self._add_reverse(",".join(parts))

    @tool(destructive=True, idempotent=True)
    def delete_reverse_server(self, network: str, server: str) -> None:
        """Delete a reverse server, formerly called conditional forwarding.

        The Pi-hole then stops learning that network's device names. FTL
        restarts to apply it, so DNS and the API pause for a second or two.
        It's refused if no reverse server forwards `network` to `server`.
        With an application password, it answers with an error (403) unless
        the Pi-hole's `webserver.api.app_sudo` setting is on.

        Args:
            network: The network, as `reverse_servers` shows it, such as
                `192.168.1.0/24`.
            server: The server it forwards to, such as `192.168.1.1`.
        """
        self._delete_reverse(_reverse_entry(self._reverse_entries(), network, server))

    @method.get("/dhcp/hosts", decoder=_decode_static_leases)
    def static_leases(self) -> StaticLeasesResponse:
        """List the static DHCP leases: addresses a device always gets.

        They apply only while the Pi-hole's DHCP server is on (`dhcp.active`).
        For the addresses it has handed out, the DHCP leases endpoint is
        better. It changes nothing.
        """
        ...

    @tool(idempotent=True)
    def add_static_lease(self, hwaddr: str, ip: str, hostname: str | None = None) -> None:
        """Add a static DHCP lease, so a device always gets the same address.

        The Pi-hole's DHCP server then gives the device with `hwaddr` the
        address `ip`, and the name `hostname` if given, from its next renewal.
        It applies only while the DHCP server is on (`dhcp.active`). FTL
        restarts to apply it, so DNS and the API pause for a second or two.
        Pi-hole answers an invalid address with an error (400), and an
        existing lease too.
        With an application password, it answers with an error (403) unless
        the Pi-hole's `webserver.api.app_sudo` setting is on.

        Args:
            hwaddr: The device's MAC address, such as `12:34:56:78:9a:bc`.
            ip: The IPv4 address it always gets, on the DHCP server's network,
                such as `192.168.1.50`.
            hostname: The name it gets, such as `laptop`, without a domain.
        """
        _check_name(hwaddr, "hwaddr")
        _check_name(ip, "ip")
        if hostname is not None:
            _check_name(hostname, "hostname")
        self._add_lease(",".join([hwaddr, ip, *([hostname] if hostname else [])]))

    @tool(destructive=True, idempotent=True)
    def delete_static_lease(self, hwaddr: str) -> None:
        """Delete a device's static DHCP lease.

        The device keeps its address until its lease ends, and may then get
        another one. FTL restarts to apply it, so DNS and the API pause for a
        second or two. It's refused if no static lease names `hwaddr`, or if
        several do.
        With an application password, it answers with an error (403) unless
        the Pi-hole's `webserver.api.app_sudo` setting is on.

        Args:
            hwaddr: The device's MAC address, as `static_leases` shows it.
        """
        self._delete_lease(_lease_entry(self._lease_entries(), hwaddr))


class AsyncConfig(AsyncResource, prefix="/config", tags=["config"]):
    """Pi-hole settings: local DNS and CNAME records, and upstream servers."""

    # Raw requests for the methods below, which build an entry, find the stored
    # one or check the arguments first. ClientX leaves private names out of AI
    # tools.
    @method.get("/dns/hosts", decoder=_decode_host_entries)
    async def _host_entries(self) -> list[str]: ...

    @method.put("/dns/hosts/{entry}")
    async def _add_host(self, entry: str) -> None: ...

    @method.delete("/dns/hosts/{entry}")
    async def _delete_host(self, entry: str) -> None: ...

    @method.get("/dns/cnameRecords", decoder=_decode_cname_entries)
    async def _cname_entries(self) -> list[str]: ...

    @method.put("/dns/cnameRecords/{entry}")
    async def _add_cname(self, entry: str) -> None: ...

    @method.delete("/dns/cnameRecords/{entry}")
    async def _delete_cname(self, entry: str) -> None: ...

    @method.patch("", decoder=_decode_upstream_servers)
    async def _patch_upstreams(
        self, config: Annotated[dict[str, object], Json(), Send(embed=True)]
    ) -> UpstreamServersResponse: ...

    @method.get("/dns/hosts", decoder=_decode_dns_records)
    async def dns_records(self) -> DnsRecordsResponse:
        """List the local DNS records: hostnames the Pi-hole answers itself.

        Devices that use the Pi-hole resolve these names, such as `nas.lan`,
        to the IP addresses given, without asking upstream. It changes
        nothing.
        """
        ...

    @tool(idempotent=True)
    async def add_dns_record(self, ip: str, hostname: str) -> None:
        """Add a local DNS record, so the Pi-hole answers `hostname` with `ip`.

        Use it to give a device on the network a name, such as `nas.lan`. It
        takes effect right away. A record that exists already answers with an
        error (400), and so does an invalid IP address or hostname.
        With an application password, it answers with an error (403) unless
        the Pi-hole's `webserver.api.app_sudo` setting is on.

        Args:
            ip: The IP address, IPv4 or IPv6, such as `192.168.1.10`.
            hostname: One hostname, such as `nas.lan`.
        """
        _check_name(ip, "ip")
        _check_name(hostname, "hostname")
        await self._add_host(f"{ip} {hostname}")

    @tool(destructive=True, idempotent=True)
    async def delete_dns_record(self, ip: str, hostname: str) -> None:
        """Delete a local DNS record, so the Pi-hole stops answering `hostname`.

        Devices then get an upstream answer for it, or none. It's refused if
        no record answers `hostname` with `ip`, or if the record names other
        hostnames too.
        With an application password, it answers with an error (403) unless
        the Pi-hole's `webserver.api.app_sudo` setting is on.

        Args:
            ip: The record's IP address, as `dns_records` shows it.
            hostname: The record's hostname, such as `nas.lan`.
        """
        await self._delete_host(_host_entry((await self._host_entries()), ip, hostname))

    @method.get("/dns/cnameRecords", decoder=_decode_cname_records)
    async def cname_records(self) -> CnameRecordsResponse:
        """List the local CNAME records: aliases the Pi-hole answers itself.

        Devices that use the Pi-hole resolve each alias, such as `files.lan`,
        as its target, such as `nas.lan`. It changes nothing.
        """
        ...

    @tool(idempotent=True)
    async def add_cname_record(self, domain: str, target: str, ttl: Annotated[int | None, Field(ge=0)] = None) -> None:
        """Add a local CNAME record, making `domain` an alias of `target`.

        The target must be a name the Pi-hole knows itself, such as a local
        DNS record or a DHCP client's hostname: dnsmasq doesn't follow an
        alias to an upstream answer. An alias can have only one target. FTL
        restarts to apply it, so DNS and the API pause for a second or two. A
        record that exists already answers with an error (400).
        With an application password, it answers with an error (403) unless
        the Pi-hole's `webserver.api.app_sudo` setting is on.

        Args:
            domain: The alias, such as `files.lan`.
            target: The domain it stands for, such as `nas.lan`.
            ttl: How long clients may cache the answer, in seconds. dnsmasq's
                local TTL, 0 unless set otherwise, by default.
        """
        _check_name(domain, "domain")
        _check_name(target, "target")
        entry = f"{domain},{target}" if ttl is None else f"{domain},{target},{ttl}"
        await self._add_cname(entry)

    @tool(destructive=True, idempotent=True)
    async def delete_cname_record(self, domain: str, target: str) -> None:
        """Delete a local CNAME record, so `domain` is no longer an alias.

        Devices then get an upstream answer for it, or none. FTL restarts to
        apply it, so DNS and the API pause for a second or two. It's refused
        if no record makes `domain` an alias of `target`, or if the record
        names other aliases too.
        With an application password, it answers with an error (403) unless
        the Pi-hole's `webserver.api.app_sudo` setting is on.

        Args:
            domain: The alias, such as `files.lan`.
            target: The domain it stands for, as `cname_records` shows it.
        """
        await self._delete_cname(_cname_entry((await self._cname_entries()), domain, target))

    @method.get("/dns/upstreams", decoder=_decode_upstream_servers)
    async def upstreams(self) -> UpstreamServersResponse:
        """List the upstream DNS servers the Pi-hole forwards queries to.

        It forwards each query it can't answer from its cache, its local
        records or its lists. For how many queries each server answered, the
        upstreams statistics are better. It changes nothing.
        """
        ...

    @tool(destructive=True, idempotent=True)
    async def set_upstreams(self, servers: Annotated[list[str], Field(min_length=1)]) -> UpstreamServersResponse:
        """Replace the upstream DNS servers the Pi-hole forwards queries to.

        Use it to switch providers, such as to Quad9's `9.9.9.9` and
        `149.112.112.112`, or to a local resolver such as `127.0.0.1#5335`.
        The list replaces the current one: to add a server, pass the current
        ones too. FTL restarts to apply it, so DNS and the API pause for a
        second or two. An invalid server answers with an error (400), and an
        empty list is refused.
        With an application password, it answers with an error (403) unless
        the Pi-hole's `webserver.api.app_sudo` setting is on.

        Args:
            servers: IP addresses or hostnames, optionally with a port after
                `#`, such as `9.9.9.9` or `127.0.0.1#5335`.
        """
        _check_servers(servers)
        return await self._patch_upstreams({"dns": {"upstreams": servers}})

    @method.get("/{element}")
    async def _detailed(self, element: str, detailed: Annotated[bool, Query()] = True) -> dict[str, Any]: ...

    @method.get("")
    async def _config_values(self) -> dict[str, Any]: ...

    @method.patch("")
    async def _patch_values(self, config: Annotated[dict[str, object], Json(), Send(embed=True)]) -> dict[str, Any]: ...

    @method.get("/dns/revServers", decoder=_decode_reverse_entries)
    async def _reverse_entries(self) -> list[str]: ...

    @method.put("/dns/revServers/{entry}")
    async def _add_reverse(self, entry: str) -> None: ...

    @method.delete("/dns/revServers/{entry}")
    async def _delete_reverse(self, entry: str) -> None: ...

    @method.get("/dhcp/hosts", decoder=_decode_lease_entries)
    async def _lease_entries(self) -> list[str]: ...

    @method.put("/dhcp/hosts/{entry}")
    async def _add_lease(self, entry: str) -> None: ...

    @method.delete("/dhcp/hosts/{entry}")
    async def _delete_lease(self, entry: str) -> None: ...

    @tool(read_only=True, idempotent=True)
    async def settings(self, key: str) -> ConfigSettingsResponse:
        """Read Pi-hole settings, with Pi-hole's own description of each.

        Each comes with its value, default, type, allowed values, and whether
        changing it restarts FTL. Read a setting before changing it with
        `update`, for the values it allows. A topic, such as `dhcp`, returns
        all its settings, and a narrower key, such as `dns.blocking`, fewer:
        `dns` has 45. It covers the `dns`, `dhcp`, `ntp`, `resolver`,
        `database` and `debug` topics, `misc.privacylevel`, and
        `webserver.api.excludeClients`, `excludeDomains` and `maxHistory`, and
        refuses other keys. It changes nothing.

        Args:
            key: A topic or a dotted key, such as `dhcp`, `dns.blocking` or
                `dns.dnssec`.
        """
        _check_key(key, "key")
        return _config_settings_response(await self._detailed(key.replace(".", "/")), key)

    @tool(destructive=True, idempotent=True)
    async def update(self, changes: Annotated[dict[str, JsonValue], Field(min_length=1)]) -> ChangedSettingsResponse:
        """Change one or more Pi-hole settings at once, all or none.

        Read them with `settings` first, for the values they allow. Pi-hole
        answers an invalid value, or a change to a setting an environment
        variable sets, with an error (400) that names it, and then changes
        nothing. If a changed setting's `restarts_ftl` is true, FTL
        restarts once, so DNS and the API pause for a second or two. It covers
        the settings `settings` reads, except `dns.port` and `dns.interface`,
        which could stop devices reaching the Pi-hole, and the lists with
        methods of their own: local DNS and CNAME records, upstreams, reverse
        servers and static leases. Turning the DHCP server on (`dhcp.active`)
        where the router serves DHCP too gives devices conflicting addresses:
        turn the router's off first.
        With an application password, it answers with an error (403) unless
        the Pi-hole's `webserver.api.app_sudo` setting is on.

        Args:
            changes: The new values by dotted key, such as
                `{"dns.dnssec": true, "misc.privacylevel": 1}`.
        """
        _check_changes(changes)
        _check_settings_exist((await self._config_values())["config"], changes)
        return _changed_settings_response(await self._patch_values(_nested(changes)), changes)

    @method.get("/dns/revServers", decoder=_decode_reverse_servers)
    async def reverse_servers(self) -> ReverseServersResponse:
        """List the reverse servers, formerly called conditional forwarding.

        Each sends the reverse lookups of a network's addresses, and the
        queries for its local domain, to a server that knows the devices'
        names, usually the router, so the statistics show names rather than
        IP addresses. It changes nothing.
        """
        ...

    @tool(idempotent=True)
    async def add_reverse_server(
        self, network: str, server: str, domain: str | None = None, enabled: bool = True
    ) -> None:
        """Add a reverse server, formerly called conditional forwarding.

        Use it so the Pi-hole learns the names of a network's devices from the
        router that gives out their addresses: it forwards the network's
        reverse lookups, and its local domain's queries, there. FTL restarts
        to apply it, so DNS and the API pause for a second or two. Pi-hole
        answers an invalid network or server with an error (400), and an
        existing reverse server too.
        With an application password, it answers with an error (403) unless
        the Pi-hole's `webserver.api.app_sudo` setting is on.

        Args:
            network: The network in CIDR notation, such as `192.168.1.0/24`.
                Without a prefix length, it's that one address only.
            server: The server to forward to, usually the router, such as
                `192.168.1.1`, optionally with a port after `#`.
            domain: The network's local domain, such as `lan` or `fritz.box`,
                whose queries go there too.
            enabled: Whether it's in effect right away.
        """
        _check_name(network, "network")
        _check_server(server)
        if domain is not None:
            _check_name(domain, "domain")
        parts = ["true" if enabled else "false", network, server, *([domain] if domain else [])]
        await self._add_reverse(",".join(parts))

    @tool(destructive=True, idempotent=True)
    async def delete_reverse_server(self, network: str, server: str) -> None:
        """Delete a reverse server, formerly called conditional forwarding.

        The Pi-hole then stops learning that network's device names. FTL
        restarts to apply it, so DNS and the API pause for a second or two.
        It's refused if no reverse server forwards `network` to `server`.
        With an application password, it answers with an error (403) unless
        the Pi-hole's `webserver.api.app_sudo` setting is on.

        Args:
            network: The network, as `reverse_servers` shows it, such as
                `192.168.1.0/24`.
            server: The server it forwards to, such as `192.168.1.1`.
        """
        await self._delete_reverse(_reverse_entry((await self._reverse_entries()), network, server))

    @method.get("/dhcp/hosts", decoder=_decode_static_leases)
    async def static_leases(self) -> StaticLeasesResponse:
        """List the static DHCP leases: addresses a device always gets.

        They apply only while the Pi-hole's DHCP server is on (`dhcp.active`).
        For the addresses it has handed out, the DHCP leases endpoint is
        better. It changes nothing.
        """
        ...

    @tool(idempotent=True)
    async def add_static_lease(self, hwaddr: str, ip: str, hostname: str | None = None) -> None:
        """Add a static DHCP lease, so a device always gets the same address.

        The Pi-hole's DHCP server then gives the device with `hwaddr` the
        address `ip`, and the name `hostname` if given, from its next renewal.
        It applies only while the DHCP server is on (`dhcp.active`). FTL
        restarts to apply it, so DNS and the API pause for a second or two.
        Pi-hole answers an invalid address with an error (400), and an
        existing lease too.
        With an application password, it answers with an error (403) unless
        the Pi-hole's `webserver.api.app_sudo` setting is on.

        Args:
            hwaddr: The device's MAC address, such as `12:34:56:78:9a:bc`.
            ip: The IPv4 address it always gets, on the DHCP server's network,
                such as `192.168.1.50`.
            hostname: The name it gets, such as `laptop`, without a domain.
        """
        _check_name(hwaddr, "hwaddr")
        _check_name(ip, "ip")
        if hostname is not None:
            _check_name(hostname, "hostname")
        await self._add_lease(",".join([hwaddr, ip, *([hostname] if hostname else [])]))

    @tool(destructive=True, idempotent=True)
    async def delete_static_lease(self, hwaddr: str) -> None:
        """Delete a device's static DHCP lease.

        The device keeps its address until its lease ends, and may then get
        another one. FTL restarts to apply it, so DNS and the API pause for a
        second or two. It's refused if no static lease names `hwaddr`, or if
        several do.
        With an application password, it answers with an error (403) unless
        the Pi-hole's `webserver.api.app_sudo` setting is on.

        Args:
            hwaddr: The device's MAC address, as `static_leases` shows it.
        """
        await self._delete_lease(_lease_entry((await self._lease_entries()), hwaddr))
