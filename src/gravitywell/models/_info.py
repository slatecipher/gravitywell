"""Models for the information endpoints, under `/info`."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from gravitywell.models._base import BaseResponse, zero_as_none


class LocalVersion(BaseModel):
    """A component as installed on the Pi-hole."""

    version: str | None = Field(description="Its version, such as `v6.1`, or `null` if the Pi-hole doesn't report one.")


class RemoteVersion(BaseModel):
    """A component's newest release, as the Pi-hole last checked."""

    version: str | None = Field(
        description="The newest version, such as `v6.2`, or `null` if the Pi-hole hasn't checked or couldn't."
    )


class ComponentVersion(BaseModel):
    """A Pi-hole component's version: as installed, and its newest release."""

    local: LocalVersion
    remote: RemoteVersion | None = Field(
        default=None, description="Its newest release, or `null` if the Pi-hole didn't say."
    )


class Versions(BaseModel):
    """The version of each component: core, web and FTL."""

    core: ComponentVersion
    web: ComponentVersion
    ftl: ComponentVersion


class VersionResponse(BaseResponse):
    """The Pi-hole's version report."""

    version: Versions


# Pi-hole's names, such as `%cpu`, or the field names a dump or an AI tool's
# result uses.
_BY_NAME_OR_ALIAS = ConfigDict(validate_by_name=True, validate_by_alias=True)
_PERCENT_OF_RAM = "FTL's share of the RAM, in percent."
_PERCENT_OF_CPU = "FTL's CPU use, in percent of one core, averaged over the last 10 seconds."


class RamUsage(BaseModel):
    """The machine's RAM, in KiB."""

    model_config = _BY_NAME_OR_ALIAS

    total: int = Field(description="All RAM, in KiB.")
    free: int = Field(description="RAM nothing uses, in KiB.")
    used: int = Field(description="RAM in use, in KiB.")
    available: int = Field(description="RAM available to new programs, including caches it can free, in KiB.")
    percent_used: float = Field(alias="%used", description="RAM in use, in percent of all RAM.")


class SwapUsage(BaseModel):
    """The machine's swap space, in KiB."""

    model_config = _BY_NAME_OR_ALIAS

    total: int = Field(description="All swap space, in KiB, or `0` if there's none.")
    free: int = Field(description="Swap space not in use, in KiB.")
    used: int = Field(description="Swap space in use, in KiB.")
    percent_used: float = Field(alias="%used", description="Swap space in use, in percent of all of it.")


class MemoryUsage(BaseModel):
    """The machine's RAM and swap space."""

    ram: RamUsage
    swap: SwapUsage


class CpuLoad(BaseModel):
    """The machine's load averages over the last 1, 5 and 15 minutes."""

    raw: list[float] = Field(description="The 1, 5 and 15-minute load averages, such as `[0.05, 0.03, 0.0]`.")
    percent: list[float] = Field(
        description="The same, in percent of all cores: `100` means every core was busy on average."
    )


class CpuUsage(BaseModel):
    """The machine's processors and how busy they are."""

    model_config = _BY_NAME_OR_ALIAS

    nprocs: int = Field(description="Processor cores.")
    percent_cpu: float = Field(
        alias="%cpu",
        description="CPU use, in percent of one core, so up to `nprocs` times 100; negative if it can't be measured.",
    )
    load: CpuLoad


class FtlUsage(BaseModel):
    """How much of the machine FTL, Pi-hole's DNS server, uses."""

    model_config = _BY_NAME_OR_ALIAS

    percent_mem: float = Field(alias="%mem", description=_PERCENT_OF_RAM)
    percent_cpu: float = Field(alias="%cpu", description=_PERCENT_OF_CPU)


class SystemInfo(BaseModel):
    """The machine the Pi-hole runs on: uptime, memory, processes and CPU."""

    uptime: int = Field(description="Seconds since the machine started.")
    memory: MemoryUsage
    procs: int = Field(description="Processes running.")
    cpu: CpuUsage
    ftl: FtlUsage


class SystemInfoResponse(BaseResponse):
    """The Pi-hole machine's resource use."""

    system: SystemInfo


class Uname(BaseModel):
    """The machine's operating system, as `uname` reports it."""

    sysname: str = Field(description="The operating system, such as `Linux`.")
    nodename: str = Field(description="The machine's hostname. In a container, often the container's ID.")
    release: str = Field(description="The kernel release, such as `6.18.50+rpt-rpi-v8`.")
    version: str = Field(description="The kernel's build version.")
    machine: str = Field(description="The processor architecture, such as `aarch64` or `x86_64`.")
    domainname: str = Field(description="The machine's NIS domain name, usually `(none)`.")


class HostInfo(BaseModel):
    """The machine the Pi-hole runs on: its operating system and model."""

    uname: Uname
    model: str | None = Field(description="The device's model, such as `Raspberry Pi 4 Model B`, or `null` if unknown.")


class HostInfoResponse(BaseResponse):
    """The Pi-hole machine's operating system and model."""

    host: HostInfo


class Temperature(BaseModel):
    """A temperature reading from a sensor."""

    name: str | None = Field(description="The reading's label, such as `Core 0`, if it has one.")
    value: float = Field(description="The temperature, in the unit `unit` gives.")
    max: float | None = Field(description="The temperature the hardware considers high, if it reports one.")
    crit: float | None = Field(description="The temperature the hardware considers critical, if it reports one.")
    sensor: str = Field(description="The sensor's input, such as `temp1`.")


class Sensor(BaseModel):
    """A hardware sensor the machine has."""

    name: str = Field(description="The sensor's name, such as `cpu_thermal`.")
    temps: list[Temperature] = Field(description="Its temperature readings, if it has any.")


class Sensors(BaseModel):
    """The machine's hardware sensors and CPU temperature."""

    model_config = _BY_NAME_OR_ALIAS

    sensors: list[Sensor] = Field(alias="list", description="Every sensor, with its temperature readings.")
    cpu_temp: float | None = Field(description="The CPU's temperature, in `unit`, or `null` if unknown.")
    hot_limit: float = Field(
        description="The temperature above which Pi-hole's dashboard shows the CPU as hot, in `unit`."
    )
    unit: str = Field(description="The unit of the temperatures: `C`, `F` or `K`.")


class SensorsResponse(BaseResponse):
    """The Pi-hole machine's hardware sensors."""

    sensors: Sensors


class EnabledCount(BaseModel):
    """How many items there are, and how many are enabled."""

    total: int = Field(description="All of them.")
    enabled: int = Field(description="The enabled ones.")


class AllowDenyCounts(BaseModel):
    """How many allow and deny rules there are."""

    allowed: EnabledCount
    denied: EnabledCount


class GravityCounts(BaseModel):
    """What the Pi-hole's gravity database holds."""

    gravity: int = Field(description="Domains on blocklists, as of the last gravity update.")
    antigravity: int = Field(description="Domains on allowlists, as of the last gravity update.")
    groups: int = Field(description="Groups.")
    lists: int = Field(description="Subscribed blocklists and allowlists.")
    clients: int = Field(description="Configured clients.")
    domains: AllowDenyCounts = Field(description="Exact allow and deny rules.")
    regex: AllowDenyCounts = Field(description="Regex allow and deny rules.")


class ClientCounts(BaseModel):
    """How many clients FTL knows."""

    total: int = Field(description="Clients in FTL's history.")
    active: int = Field(description="Clients that sent queries in FTL's history.")


class FtlInfo(BaseModel):
    """FTL, Pi-hole's DNS server: its database, settings and resource use."""

    model_config = _BY_NAME_OR_ALIAS

    database: GravityCounts
    privacy_level: int = Field(
        description="What statistics hide: `0` nothing, `1` domains, `2` domains and clients, `3` everything, with "
        "no query log or long-term database."
    )
    clients: ClientCounts
    pid: int = Field(description="FTL's process ID.")
    uptime: float = Field(description="Milliseconds since FTL started, such as `11823660.2` for about 3.3 hours.")
    percent_mem: float = Field(alias="%mem", description=_PERCENT_OF_RAM)
    percent_cpu: float = Field(alias="%cpu", description=_PERCENT_OF_CPU)
    allow_destructive: bool = Field(
        description="Whether the API allows destructive actions, such as restarting the DNS server or flushing logs."
    )


class FtlInfoResponse(BaseResponse):
    """FTL's database contents, settings and resource use."""

    ftl: FtlInfo


class DatabaseInfoResponse(BaseResponse):
    """The query database: its size and the queries it holds."""

    size: int = Field(description="The database file's size, in bytes.")
    queries: int = Field(description="Queries in memory.")
    earliest_timestamp: Annotated[datetime | None, BeforeValidator(zero_as_none)] = Field(
        description="When the oldest query in memory arrived, in UTC, or `null` if there's none."
    )
    queries_disk: int = Field(description="Queries in the database file.")
    earliest_timestamp_disk: Annotated[datetime | None, BeforeValidator(zero_as_none)] = Field(
        description="When the oldest query in the database file arrived, in UTC, as of FTL's start or its last "
        "cleanup of old queries, or `null` if it had none then, though it may have queries since."
    )
    sqlite_version: str = Field(description="The SQLite version FTL uses, such as `3.54.1`.")


class CacheCount(BaseModel):
    """How many cache entries of a type are fresh, and how many stale."""

    valid: int = Field(description="Entries still within their time to live.")
    stale: int = Field(description="Expired entries kept to answer while a fresh answer is fetched.")


class CacheContent(BaseModel):
    """The DNS cache's entries of one record type."""

    type: int = Field(description="The DNS record type's number, such as `1` for `A`.")
    name: str = Field(description="The record type, such as `A` or `AAAA`, or `OTHER` for the rest.")
    count: CacheCount


class DnsCache(BaseModel):
    """FTL's DNS cache."""

    size: int = Field(description="How many entries the cache holds at most.")
    inserted: int = Field(description="Entries added since FTL started.")
    evicted: int = Field(
        description="Entries removed before they expired, to make room. If it keeps growing, the cache is too small."
    )
    expired: int = Field(description="Entries removed after they expired.")
    immortal: int = Field(description="Entries that never expire, such as from local configuration.")
    content: list[CacheContent] = Field(description="The entries now in the cache, by record type.")


class DnsReplies(BaseModel):
    """How FTL answered queries since it started."""

    local: int = Field(description="Answered from the cache or local configuration.")
    forwarded: int = Field(description="Forwarded to an upstream server.")
    optimized: int = Field(description="Answered from a stale cache entry while a fresh answer was fetched.")
    unanswered: int = Field(description="Never answered.")
    auth: int = Field(description="Answered authoritatively, for a zone the Pi-hole serves.")
    sum: int = Field(description="All of these together.")


class DnsMetrics(BaseModel):
    """FTL's DNS cache and replies."""

    cache: DnsCache
    replies: DnsReplies


class DhcpLeases(BaseModel):
    """DHCP leases since FTL started."""

    allocated_4: int = Field(description="IPv4 leases handed out.")
    pruned_4: int = Field(description="IPv4 leases removed after they expired.")
    allocated_6: int = Field(description="IPv6 leases handed out.")
    pruned_6: int = Field(description="IPv6 leases removed after they expired.")


class DhcpMetrics(BaseModel):
    """FTL's DHCP messages since it started, all zero if it serves no DHCP."""

    ack: int = Field(description="DHCPACK messages sent.")
    decline: int = Field(description="DHCPDECLINE messages received.")
    discover: int = Field(description="DHCPDISCOVER messages received.")
    inform: int = Field(description="DHCPINFORM messages received.")
    nak: int = Field(description="DHCPNAK messages sent.")
    offer: int = Field(description="DHCPOFFER messages sent.")
    release: int = Field(description="DHCPRELEASE messages received.")
    request: int = Field(description="DHCPREQUEST messages received.")
    noanswer: int = Field(description="Requests left unanswered.")
    bootp: int = Field(description="BOOTP requests received.")
    pxe: int = Field(description="PXE requests received.")
    leases: DhcpLeases


class Metrics(BaseModel):
    """FTL's DNS and DHCP counters since it started."""

    dns: DnsMetrics
    dhcp: DhcpMetrics


class MetricsResponse(BaseResponse):
    """FTL's DNS cache, DNS replies and DHCP counters."""

    metrics: Metrics


class DiagnosisMessage(BaseModel):
    """A problem the Pi-hole reports, as on its dashboard's diagnosis page."""

    id: int = Field(description="The message's ID, to delete it by.")
    timestamp: datetime = Field(description="When the Pi-hole reported it, in UTC.")
    type: str = Field(
        description="What it's about: `REGEX` (an invalid regex rule), `SUBNET` (a client matched by several subnet "
        "clients), `HOSTNAME` (a client's hostname with invalid characters), `DNSMASQ_CONFIG` (an error in the DNS "
        "server's configuration), `DNSMASQ_WARN` (a warning from the DNS server), `RATE_LIMIT` (a client limited for "
        "sending too many queries), `LOAD` (load above the number of cores), `SHMEM` (shared memory running out), "
        "`DISK` and `DISK_EXTENDED` (a disk running full), `LIST` (a list unavailable in the last gravity update), "
        "`CERTIFICATE_DOMAIN_MISMATCH` (the HTTPS certificate doesn't match the domain), `CONNECTION_ERROR` (an "
        "upstream server unreachable), `NTP` (a time synchronization problem), `VERIFY` (FTL's binary failed its "
        "check), `GRAVITY_RESTORED` (a failed gravity update was rolled back) or `TELEPORTER_SKIPPED` (a setting a "
        "Teleporter import skipped)."
    )
    plain: str = Field(description="The message, such as `Rate-limiting 192.168.2.42 for at least 5 seconds`.")
    html: str = Field(description="The same message in HTML, sometimes with more detail, such as the limit applied.")


class MessagesResponse(BaseResponse):
    """The problems the Pi-hole reports."""

    messages: list[DiagnosisMessage] = Field(description="The messages, oldest first. Empty if there are none.")


class MessageCountResponse(BaseResponse):
    """How many problems the Pi-hole reports."""

    count: int = Field(description="Diagnosis messages.")
