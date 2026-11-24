"""The configuration endpoints, under `/config`.

Only the settings people change most: local DNS and CNAME records, and the
upstream DNS servers. Changing settings with an application password needs the
Pi-hole's `webserver.api.app_sudo` setting on.
"""

import re
from typing import Annotated, Any

from clientx import ArgumentError, AsyncResource, Json, Resource, Response, Send, method
from clientx.tools import tool
from pydantic import Field

from gravitywell.models import (
    CnameRecord,
    CnameRecordsResponse,
    DnsRecord,
    DnsRecordsResponse,
    UpstreamServersResponse,
)

# FTL reads a `#` at an entry's start or after whitespace as a comment.
_COMMENT = re.compile(r"(?:^|\s)#.*")
# What would split an argument into several names in an entry.
_SEPARATOR = re.compile(r"[\s,#]")


def _dns_setting(response: Response, name: str) -> tuple[float, list[str]]:
    """Read `took` and the setting `dns.<name>` from a config response."""
    body: dict[str, Any] = response.json()
    return body["took"], body["config"]["dns"][name]


def _dns_record(entry: str) -> DnsRecord:
    ip, *hostnames = _COMMENT.sub("", entry).split()
    return DnsRecord(ip=ip, hostnames=hostnames)


def _cname_record(entry: str) -> CnameRecord:
    parts = [part.strip() for part in _COMMENT.sub("", entry).split(",")]
    ttl = int(parts.pop()) if parts[-1].isdecimal() else None
    return CnameRecord(domains=parts[:-1], target=parts[-1], ttl=ttl)


def _decode_dns_records(response: Response) -> DnsRecordsResponse:
    took, entries = _dns_setting(response, "hosts")
    return DnsRecordsResponse(took=took, records=[_dns_record(entry) for entry in entries])


def _decode_cname_records(response: Response) -> CnameRecordsResponse:
    took, entries = _dns_setting(response, "cnameRecords")
    return CnameRecordsResponse(took=took, records=[_cname_record(entry) for entry in entries])


def _decode_upstream_servers(response: Response) -> UpstreamServersResponse:
    took, servers = _dns_setting(response, "upstreams")
    return UpstreamServersResponse(took=took, servers=servers)


def _decode_host_entries(response: Response) -> list[str]:
    return _dns_setting(response, "hosts")[1]


def _decode_cname_entries(response: Response) -> list[str]:
    return _dns_setting(response, "cnameRecords")[1]


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


class Config(Resource, prefix="/config"):
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
    def _patch(self, config: Annotated[dict[str, object], Json(), Send(embed=True)]) -> UpstreamServersResponse: ...

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
        return self._patch({"dns": {"upstreams": servers}})


class AsyncConfig(AsyncResource, prefix="/config"):
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
    async def _patch(
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
        return await self._patch({"dns": {"upstreams": servers}})
