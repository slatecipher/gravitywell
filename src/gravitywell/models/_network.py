"""Models for the network endpoints, under `/network`."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from gravitywell.models._base import BaseResponse, zero_as_none

# Pi-hole's names, such as `lastQuery`, or the field names a dump or an AI
# tool's result uses.
_BY_NAME_OR_ALIAS = ConfigDict(validate_by_name=True, validate_by_alias=True)
_UnknownTime = Annotated[datetime | None, BeforeValidator(zero_as_none)]


class DeviceAddress(BaseModel):
    """An IP address a device used, and its hostname."""

    model_config = _BY_NAME_OR_ALIAS

    ip: str = Field(description="The IP address, such as `192.168.1.235`.")
    name: str | None = Field(description="The hostname it resolves to, such as `laptop.lan`, or `null` if none.")
    last_seen: datetime = Field(alias="lastSeen", description="When the Pi-hole last saw the device at it, in UTC.")
    name_updated: _UnknownTime = Field(
        alias="nameUpdated", description="When its hostname last changed, in UTC, or `null` if it has none."
    )


class NetworkDevice(BaseModel):
    """A device on the network the Pi-hole has seen, from its network table."""

    model_config = _BY_NAME_OR_ALIAS

    id: int = Field(description="The device's ID in the network table, to delete it by.")
    hwaddr: str = Field(
        description="Its MAC address, such as `0e:18:ee:8b:97:9b`, or `ip-` and its IP address when the Pi-hole "
        "doesn't know its MAC address, such as `ip-192.168.1.235`."
    )
    interface: str = Field(description="The Pi-hole's network interface it was seen on, such as `eth0`.")
    first_seen: datetime = Field(alias="firstSeen", description="When the Pi-hole first saw it, in UTC.")
    last_query: _UnknownTime = Field(
        alias="lastQuery", description="When it last sent the Pi-hole a query, in UTC, or `null` if never."
    )
    num_queries: int = Field(alias="numQueries", description="Queries it has sent the Pi-hole.")
    mac_vendor: str = Field(
        alias="macVendor", description="The maker its MAC address belongs to, or an empty string if unknown."
    )
    ips: list[DeviceAddress] = Field(description="Up to `max_addresses` of its IP addresses.")


class NetworkDevicesResponse(BaseResponse):
    """The devices the Pi-hole has seen on the network."""

    devices: list[NetworkDevice] = Field(description="Up to `max_devices` devices, the most recently active first.")


class Gateway(BaseModel):
    """A default route, for one address family."""

    family: str = Field(description="The address family: `inet` for IPv4, `inet6` for IPv6.")
    interface: str = Field(description="The Pi-hole's network interface it goes through, such as `eth0`.")
    address: str = Field(description="The gateway's IP address, such as `192.168.1.1`.")
    local: list[str] = Field(description="The Pi-hole's own IP addresses on that interface.")


class GatewayResponse(BaseResponse):
    """The Pi-hole's default routes."""

    gateway: list[Gateway] = Field(description="A default route for each address family that has one.")


class InterfaceTraffic(BaseModel):
    """An amount of traffic, as a value and a binary prefix."""

    value: float = Field(description="The amount, such as `4.66`.")
    unit: str = Field(
        description="The prefix, in steps of 1024: an empty string for bytes, `k` for KiB, `M` for MiB, `G` for GiB."
    )


class InterfaceStats(BaseModel):
    """An interface's traffic since it came up."""

    rx_bytes: InterfaceTraffic = Field(description="Data received.")
    tx_bytes: InterfaceTraffic = Field(description="Data sent.")


class InterfaceAddress(BaseModel):
    """An IP address an interface has."""

    family: str = Field(description="The address family: `inet` for IPv4, `inet6` for IPv6.")
    address: str = Field(description="The IP address, such as `172.18.0.2`.")
    prefixlen: int = Field(description="The prefix length of its network, such as `24`.")
    scope: str = Field(description="Where it's valid: `host`, `link` or `universe` (everywhere).")


class NetworkInterface(BaseModel):
    """A network interface of the Pi-hole's machine."""

    name: str = Field(description="The interface's name, such as `eth0` or `lo`.")
    type: str = Field(description="Its kind, such as `ether` or `loopback`.")
    state: str = Field(description="Its state, such as `up`, `down` or `unknown`.")
    carrier: bool = Field(description="Whether it has a link, such as a connected cable.")
    speed: int | None = Field(description="Its link speed, in Mbit/s, or `null` if it has none, as a loopback.")
    address: str = Field(description="Its MAC address.")
    addresses: list[InterfaceAddress] = Field(description="Its IP addresses.")
    stats: InterfaceStats


class InterfacesResponse(BaseResponse):
    """The network interfaces of the Pi-hole's machine."""

    interfaces: list[NetworkInterface] = Field(description="The interfaces.")


class Route(BaseModel):
    """A route in the Pi-hole machine's routing tables."""

    dst: str = Field(description="Where it leads: `default`, or a network or address such as `172.18.0.0`.")
    gateway: str | None = Field(default=None, description="The router it goes through, if any.")
    oif: str = Field(description="The interface it goes out on, such as `eth0`.")
    prefsrc: str | None = Field(default=None, description="The source address it prefers, if it has one.")
    family: str = Field(description="The address family: `inet` for IPv4, `inet6` for IPv6.")
    type: str = Field(description="Its kind, such as `unicast`, `local` or `broadcast`.")
    table: int = Field(description="Its routing table: `254` is the main table, `255` the local one.")
    protocol: str = Field(description="What added it, such as `kernel` or `boot`.")
    scope: str = Field(description="How far it reaches: `host`, `link` or `universe` (everywhere).")


class RoutesResponse(BaseResponse):
    """The Pi-hole machine's routes."""

    routes: list[Route] = Field(description="The routes, from every routing table.")
