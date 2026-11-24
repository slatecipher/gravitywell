"""Models for the insights tools, which combine several API calls in one."""

from typing import Literal

from pydantic import BaseModel, Field

from gravitywell.models._base import BLOCKING_STATUS, BlockingStatus
from gravitywell.models._clients import ConfiguredClient
from gravitywell.models._domains import DomainRule
from gravitywell.models._info import DiagnosisMessage, SystemInfo
from gravitywell.models._lists import SubscribedList
from gravitywell.models._network import NetworkDevice
from gravitywell.models._padd import PaddSensors
from gravitywell.models._queries import LoggedQuery
from gravitywell.models._search import ListMatch

_GROUP_NAMES = (
    "The names of the groups these refer to, by ID. A rule, list or client record affects only clients in its groups."
)


class DomainExplanation(BaseModel):
    """What the Pi-hole does with a domain, and why."""

    domain: str = Field(description="The domain asked about.")
    blocking: BlockingStatus = Field(description=BLOCKING_STATUS + " Unless `enabled`, nothing is blocked.")
    rules: list[DomainRule] = Field(description="The allow and deny rules that match it, exact and regex.")
    lists: list[ListMatch] = Field(description="The blocklists and allowlists that contain it.")
    groups: dict[int, str] = Field(description=_GROUP_NAMES)
    recent_queries: list[LoggedQuery] = Field(
        description="Its newest queries, newest first: each one's `status` says what the Pi-hole did, and `client` "
        "for whom."
    )


class ClientExplanation(BaseModel):
    """Who a client is, which groups it's in, and what it asked for."""

    address: str = Field(description="The IP address asked about.")
    device: NetworkDevice | None = Field(
        description="The device with this address in the Pi-hole's network table: its MAC address, maker, "
        "hostnames and activity. `null` if the Pi-hole hasn't seen it."
    )
    clients: list[ConfiguredClient] = Field(
        description="The client records that match it, in the order Pi-hole tries them: IP address, subnet, MAC "
        "address, hostname, interface. The first sets its groups; with none, it's in the Default group, `0`, only."
    )
    groups: dict[int, str] = Field(description=_GROUP_NAMES)
    recent_queries: list[LoggedQuery] = Field(description="Its newest queries, newest first.")


class ComponentUpdate(BaseModel):
    """A Pi-hole component with a newer release than the one installed."""

    component: Literal["core", "web", "ftl"] = Field(
        description="`core` (the scripts), `web` (the web interface) or `ftl` (the DNS server and API)."
    )
    installed: str = Field(description="The version installed, such as `v6.1`.")
    available: str = Field(description="The newest version, such as `v6.2`.")


class HealthReport(BaseModel):
    """How the Pi-hole is doing, and what's wrong with it, if anything."""

    findings: list[str] = Field(
        description="The problems found, in plain words, the most urgent first. Empty if all is well. RAM counts "
        "from 90% used, and load from 100% of the CPU's cores over 5 minutes."
    )
    blocking: BlockingStatus = Field(description=BLOCKING_STATUS)
    blocking_timer: float | None = Field(
        description="Seconds until blocking changes back, if a timer is set, or `null`."
    )
    messages: list[DiagnosisMessage] = Field(description="The problems the Pi-hole itself reported.")
    updates: list[ComponentUpdate] = Field(description="The components with a newer release available.")
    problem_lists: list[SubscribedList] = Field(
        description="Enabled lists whose last gravity update didn't download them: `status` `0` never downloaded, "
        "`3` unavailable so an older copy is in use, `4` unavailable with no copy, so its domains aren't blocked."
    )
    gravity_size: int = Field(description="Domains on the blocklists, as of the last gravity update.")
    system: SystemInfo
    sensors: PaddSensors
