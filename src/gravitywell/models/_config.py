"""Models for the configuration endpoints, under `/config`."""

from pydantic import BaseModel, Field, JsonValue

from gravitywell.models._base import BaseResponse


class DnsRecord(BaseModel):
    """A local DNS record: hostnames the Pi-hole answers with an IP address."""

    ip: str = Field(description="The IP address, IPv4 or IPv6, such as `192.168.1.10`.")
    hostnames: list[str] = Field(description="The hostnames it answers for, such as `nas.lan`. Usually one.")


class DnsRecordsResponse(BaseResponse):
    """The Pi-hole's local DNS records."""

    records: list[DnsRecord] = Field(description="The records, the oldest first.")


class CnameRecord(BaseModel):
    """A local CNAME record: aliases the Pi-hole answers with another domain."""

    domains: list[str] = Field(description="The aliases, such as `files.lan`. Usually one.")
    target: str = Field(description="The domain they stand for, such as `nas.lan`.")
    ttl: int | None = Field(
        description="How long clients may cache the answer, in seconds, or `null` for dnsmasq's local TTL, 0 "
        "unless `misc.dnsmasq_lines` sets `local-ttl`."
    )


class CnameRecordsResponse(BaseResponse):
    """The Pi-hole's local CNAME records."""

    records: list[CnameRecord] = Field(description="The records, the oldest first.")


class UpstreamServersResponse(BaseResponse):
    """The DNS servers the Pi-hole forwards the queries it can't answer to."""

    servers: list[str] = Field(
        description="The servers: IP addresses or hostnames, optionally with a port after `#`, such as `9.9.9.9` or "
        "`127.0.0.1#5335`."
    )


class AllowedValue(BaseModel):
    """One of the values a setting allows."""

    item: JsonValue = Field(description="The value, such as `NULL` or `1`.")
    description: str = Field(description="What it does.")


class ConfigSetting(BaseModel):
    """A Pi-hole setting, with Pi-hole's own description of it."""

    key: str = Field(description="Its key, such as `dns.dnssec`, to change it by.")
    description: str = Field(description="What it does, in Pi-hole's words.")
    type: str = Field(description="Its type, such as `boolean`, `integer`, `string array` or `enum (string)`.")
    value: JsonValue = Field(description="Its current value.")
    default: JsonValue = Field(description="Its default value.")
    allowed: str | list[AllowedValue] | None = Field(
        description="What it accepts: a description, the choices of an enum, or `null` for any value of its type."
    )
    modified: bool = Field(description="Whether its value differs from the default.")
    restarts_ftl: bool = Field(
        description="Whether changing it restarts FTL, so DNS and the API pause for a second or two."
    )
    set_by_environment: bool = Field(
        description="Whether an environment variable sets it, so it can't be changed through the API."
    )


class ConfigSettingsResponse(BaseResponse):
    """Pi-hole settings, with Pi-hole's own descriptions of them."""

    settings: list[ConfigSetting] = Field(description="The settings under the key asked for.")


class ChangedSettingsResponse(BaseResponse):
    """The settings a change set, with their new values."""

    settings: dict[str, JsonValue] = Field(description="Each setting's value after the change, by its key.")


class ReverseServer(BaseModel):
    """A reverse server, formerly conditional forwarding.

    The Pi-hole forwards the reverse lookups of a network's addresses, and the
    queries for its local domain, to a server that knows its devices' names,
    usually the router.
    """

    enabled: bool = Field(description="Whether it's in effect.")
    network: str = Field(description="The network, in CIDR notation, such as `192.168.1.0/24`.")
    server: str = Field(
        description="The server it forwards to, such as `192.168.1.1`, optionally with a port after `#`."
    )
    domain: str | None = Field(
        description="The network's local domain, such as `lan` or `fritz.box`, also forwarded, or `null`."
    )


class ReverseServersResponse(BaseResponse):
    """The Pi-hole's reverse servers, formerly conditional forwarding."""

    servers: list[ReverseServer] = Field(description="The reverse servers, the oldest first.")


class StaticLease(BaseModel):
    """A static DHCP lease: an address the DHCP server always gives a device."""

    hwaddr: str | None = Field(description="The device's MAC address, such as `12:34:56:78:9a:bc`.")
    ip: str | None = Field(description="The IP address it always gets, such as `192.168.1.50`, or `null`.")
    hostname: str | None = Field(description="The hostname it gets, such as `laptop`, or `null`.")
    lease_time: str | None = Field(
        description="How long the lease lasts, such as `24h` or `infinite`, or `null` for the `dhcp.leaseTime` setting."
    )


class StaticLeasesResponse(BaseResponse):
    """The static leases of the Pi-hole's DHCP server."""

    leases: list[StaticLease] = Field(description="The static leases, the oldest first.")
