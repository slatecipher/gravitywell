"""The logic of the insights tools, which combine several API calls in one.

The clients' `explain_domain`, `explain_client` and `check_health` make the
requests, sync or async, and these functions build the answer from the replies.
"""

import ipaddress
from collections.abc import Iterable
from typing import Literal

from clientx import ArgumentError

from gravitywell.models import (
    BlockingResponse,
    ClientExplanation,
    ClientsResponse,
    ComponentUpdate,
    ComponentVersion,
    ConfiguredClient,
    DomainExplanation,
    GroupsResponse,
    HealthReport,
    ListsResponse,
    MessagesResponse,
    NetworkDevice,
    NetworkDevicesResponse,
    PaddResponse,
    QueryLogResponse,
    SearchResponse,
    SubscribedList,
    VersionResponse,
)

# Enough to find any device on a home or office network, and all its addresses.
MAX_DEVICES = 1000
MAX_ADDRESSES = 100
# The thresholds `check_health` reports from, in percent.
_RAM_LIMIT = 90.0
_LOAD_LIMIT = 100.0
_COMPONENT_NAMES = {"core": "Pi-hole's core", "web": "the web interface", "ftl": "FTL"}


def _ip(value: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    try:
        return ipaddress.ip_address(value)
    except ValueError:
        return None


def check_address(address: str) -> None:
    """Refuse an address that isn't an IP address, before any request."""
    if _ip(address) is None:
        raise ArgumentError(f"`{address}` isn't an IP address, such as `192.168.1.235`.", parameter="address")


def _group_names(groups: GroupsResponse, ids: Iterable[int]) -> dict[int, str]:
    wanted = set(ids)
    return {group.id: group.name for group in groups.groups if group.id in wanted}


def explain_domain(
    domain: str, blocking: BlockingResponse, search: SearchResponse, groups: GroupsResponse, queries: QueryLogResponse
) -> DomainExplanation:
    rules, lists = search.search.domains, search.search.gravity
    return DomainExplanation(
        domain=domain,
        blocking=blocking.blocking,
        rules=rules,
        lists=lists,
        groups=_group_names(groups, (group for item in [*rules, *lists] for group in item.groups)),
        recent_queries=queries.queries,
    )


def _match_rank(record: ConfiguredClient, address: str, device: NetworkDevice | None) -> int | None:
    """Rank how a client record matches, in the order Pi-hole tries them.

    FTL looks for the client's IP address, or a subnet holding it, then its MAC
    address, its hostname and its interface, and the first kind that matches
    sets its groups. `None` if the record doesn't match.
    """
    value = record.client
    if _ip(value) == _ip(address):
        return 0
    if "/" in value:
        try:
            if ipaddress.ip_address(address) in ipaddress.ip_network(value, strict=False):
                return 1
        except ValueError:
            return None
    if device is None:
        return None
    if value.lower() == device.hwaddr.lower():
        return 2
    if value.lower() in {ip.name.lower() for ip in device.ips if ip.name}:
        return 3
    if value == f":{device.interface}":
        return 4
    return None


def explain_client(
    address: str,
    devices: NetworkDevicesResponse,
    clients: ClientsResponse,
    groups: GroupsResponse,
    queries: QueryLogResponse,
) -> ClientExplanation:
    target = _ip(address)
    device = next((each for each in devices.devices if any(_ip(ip.ip) == target for ip in each.ips)), None)
    ranked = [
        (rank, record) for record in clients.clients if (rank := _match_rank(record, address, device)) is not None
    ]
    matches = [record for _, record in sorted(ranked, key=lambda pair: pair[0])]
    return ClientExplanation(
        address=address,
        device=device,
        clients=matches,
        groups=_group_names(groups, (group for record in matches for group in record.groups)),
        recent_queries=queries.queries,
    )


def _lists(count: int) -> str:
    return "1 enabled list" if count == 1 else f"{count} enabled lists"


def _blocking_findings(blocking: BlockingResponse, gravity_size: int) -> list[str]:
    findings: list[str] = []
    if blocking.blocking in ("failure", "failed"):
        findings.append("The DNS server isn't running, so the Pi-hole answers no queries.")
    elif blocking.blocking == "disabled":
        until = f": it resumes in {blocking.timer:.0f} seconds" if blocking.timer else ""
        findings.append(f"Blocking is disabled, so every domain gets through{until}.")
    elif blocking.blocking == "unknown":
        findings.append("The blocking status isn't known yet, as while the Pi-hole starts.")
    if gravity_size == 0:
        findings.append("The blocklists hold no domains: add a list, or run a gravity update.")
    return findings


def _list_findings(problem_lists: list[SubscribedList]) -> tuple[list[str], list[str]]:
    """Find the lists in effect no more, and those that can wait."""
    missing = sum(each.status == 4 for each in problem_lists)
    stale = sum(each.status == 3 for each in problem_lists)
    new = sum(each.status == 0 for each in problem_lists)
    urgent: list[str] = []
    later: list[str] = []
    if missing:
        urgent.append(f"{_lists(missing)} couldn't be downloaded and have no copy, so their domains aren't in effect.")
    if stale:
        later.append(f"{_lists(stale)} couldn't be downloaded in the last gravity update, so an older copy is in use.")
    if new:
        later.append(f"{_lists(new)} {'hasn' if new == 1 else 'haven'}'t been downloaded yet: run a gravity update.")
    return urgent, later


def _system_findings(padd: PaddResponse) -> list[str]:
    findings: list[str] = []
    sensors, system = padd.sensors, padd.system
    if sensors.cpu_temp is not None and sensors.cpu_temp >= sensors.hot_limit:
        findings.append(
            f"The CPU is at {sensors.cpu_temp:.0f}°{sensors.unit}, at or above the "
            f"{sensors.hot_limit:.0f}°{sensors.unit} limit."
        )
    if system.memory.ram.percent_used >= _RAM_LIMIT:
        findings.append(f"RAM is {system.memory.ram.percent_used:.0f}% used.")
    if len(system.cpu.load.percent) > 1 and system.cpu.load.percent[1] >= _LOAD_LIMIT:
        findings.append(f"The 5-minute load is {system.cpu.load.percent[1]:.0f}% of the CPU's cores.")
    return findings


def _updates(versions: VersionResponse) -> list[ComponentUpdate]:
    components: tuple[tuple[Literal["core", "web", "ftl"], ComponentVersion], ...] = (
        ("core", versions.version.core),
        ("web", versions.version.web),
        ("ftl", versions.version.ftl),
    )
    return [
        ComponentUpdate(component=component, installed=installed, available=available)
        for component, version in components
        if version.remote
        and (installed := version.local.version)
        and (available := version.remote.version)
        and installed != available
    ]


def check_health(
    blocking: BlockingResponse,
    messages: MessagesResponse,
    versions: VersionResponse,
    lists: ListsResponse,
    padd: PaddResponse,
) -> HealthReport:
    problem_lists = [each for each in lists.lists if each.enabled and each.status in (0, 3, 4)]
    urgent_lists, later_lists = _list_findings(problem_lists)
    count = len(messages.messages)
    reported = [f"The Pi-hole reported {count} problem{'' if count == 1 else 's'}, in `messages`."] if count else []
    updates = _updates(versions)
    findings = [
        *_blocking_findings(blocking, padd.gravity_size),
        *urgent_lists,
        *reported,
        *_system_findings(padd),
        *later_lists,
        *(
            f"An update is available for {_COMPONENT_NAMES[update.component]}: {update.installed} to "
            f"{update.available}."
            for update in updates
        ),
    ]
    return HealthReport(
        findings=findings,
        blocking=blocking.blocking,
        blocking_timer=blocking.timer,
        messages=messages.messages,
        updates=updates,
        problem_lists=problem_lists,
        gravity_size=padd.gravity_size,
        system=padd.system,
        sensors=padd.sensors,
    )
