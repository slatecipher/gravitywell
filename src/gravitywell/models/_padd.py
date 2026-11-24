"""Models for PADD's summary, under `/padd`."""

from pydantic import BaseModel, ConfigDict, Field

from gravitywell.models._base import BLOCKING_STATUS, BaseResponse, BlockingStatus
from gravitywell.models._info import SystemInfo, Versions
from gravitywell.models._network import InterfaceTraffic


class PaddQueries(BaseModel):
    """The queries of the last 24 hours."""

    total: int = Field(description="Queries in the last 24 hours.")
    blocked: int = Field(description="Of those, the ones blocked.")
    percent_blocked: float = Field(description="The share blocked, in percent.")
    query_frequency: float = Field(description="Queries per second, averaged over the last 30 seconds.")


class PaddCache(BaseModel):
    """The DNS cache."""

    size: int = Field(description="Entries the cache holds at most.")
    inserted: int = Field(description="Entries added to it.")
    evicted: int = Field(
        description="Entries dropped before they expired, as the cache was full. If it grows, the cache is too small."
    )


class PaddInterface(BaseModel):
    """The network interface of the Pi-hole's machine for an address family."""

    name: str = Field(description="The interface's name, such as `eth0`.")
    addr: str | None = Field(description="Its address, such as `192.168.1.2`, or `null` if it has none.")
    num_addrs: int = Field(description="How many addresses of this family it has.")
    gw_addr: str | None = Field(description="The gateway's address, or `null` if there's none.")
    rx_bytes: InterfaceTraffic | None = Field(default=None, description="Data received, for IPv4 only.")
    tx_bytes: InterfaceTraffic | None = Field(default=None, description="Data sent, for IPv4 only.")


class PaddInterfaces(BaseModel):
    """The Pi-hole machine's network interfaces, by address family."""

    v4: PaddInterface
    v6: PaddInterface


class PaddConfig(BaseModel):
    """A digest of the Pi-hole's key settings."""

    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)

    dhcp_active: bool = Field(description="Whether its DHCP server is on.")
    dhcp_start: str = Field(description="The first address the DHCP server gives out, or an empty string.")
    dhcp_end: str = Field(description="The last address the DHCP server gives out, or an empty string.")
    dhcp_ipv6: bool = Field(description="Whether the DHCP server serves IPv6 too.")
    dns_domain: str = Field(description="The local domain, such as `lan`.")
    dns_port: int = Field(description="The port DNS listens on, normally `53`.")
    dns_num_upstreams: int = Field(description="How many upstream DNS servers it forwards to.")
    dns_dnssec: bool = Field(description="Whether it validates DNSSEC.")
    dns_rev_server_active: bool = Field(
        alias="dns_revServer_active", description="Whether a reverse server, formerly conditional forwarding, is set."
    )
    privacy_level: int = Field(description="The privacy level, `0` (show everything) to `3` (anonymize everything).")


class PaddSensors(BaseModel):
    """The machine's temperature."""

    cpu_temp: float | None = Field(description="The CPU's temperature, in `unit`, or `null` if unknown.")
    hot_limit: float = Field(description="The temperature above which the web interface warns, in `unit`.")
    unit: str = Field(description="The unit: `C`, `F` or `K`.")


class PaddResponse(BaseResponse):
    """A summary of the Pi-hole's state, as PADD's dashboard shows it."""

    blocking: BlockingStatus = Field(description=BLOCKING_STATUS)
    queries: PaddQueries
    gravity_size: int = Field(description="Domains on the blocklists, as of the last gravity update.")
    active_clients: int = Field(description="Clients that sent queries in the last 24 hours.")
    top_domain: str | None = Field(description="The most queried domain, or `null` if none or hidden.")
    top_blocked: str | None = Field(description="The most blocked domain, or `null` if none or hidden.")
    top_client: str | None = Field(description="The client that sent the most queries, by name or IP address.")
    recent_blocked: str | None = Field(description="The domain blocked last, or `null` if none or hidden.")
    cache: PaddCache
    system: SystemInfo
    sensors: PaddSensors
    config: PaddConfig
    node_name: str = Field(description="The machine's hostname.")
    host_model: str | None = Field(description="The machine's model, such as a Raspberry Pi's, or `null`.")
    iface: PaddInterfaces | None = Field(default=None, description="The network interfaces, only with `full`.")
    version: Versions | None = Field(
        default=None, description="The versions of the Pi-hole's components, and the newest ones, only with `full`."
    )
