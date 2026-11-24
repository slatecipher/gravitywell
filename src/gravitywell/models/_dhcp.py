"""Models for the DHCP endpoints, under `/dhcp`."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, Field

from gravitywell.models._base import BaseResponse, zero_as_none


class DhcpLease(BaseModel):
    """An IP address the Pi-hole's DHCP server has leased to a device."""

    expires: Annotated[datetime | None, BeforeValidator(zero_as_none)] = Field(
        description="When the lease ends, in UTC, or `null` if it never does."
    )
    name: str = Field(description="The device's hostname, such as `laptop`, or `*` if it gave none.")
    hwaddr: str = Field(description="The device's MAC address, such as `12:34:56:78:9a:bc`.")
    ip: str = Field(description="The leased IP address, such as `192.168.1.50`.")
    clientid: str = Field(description="The DHCP client ID the device sent, or `*` if none.")


class DhcpLeasesResponse(BaseResponse):
    """The leases the Pi-hole's DHCP server has handed out."""

    leases: list[DhcpLease] = Field(description="The leases. Empty if the Pi-hole doesn't serve DHCP.")
