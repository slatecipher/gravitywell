from collections.abc import Callable, Mapping
from typing import Any

import httpx2
import pytest
from clientx import ArgumentError
from clientx.tools import list_tools

from gravitywell import AsyncPiHole, PiHole, PiHoleAuth

BASE_URL = "http://pi.hole"
PASSWORD = "app-password"
# conftest.py's `route` fixture.
type Route = Callable[[Mapping[str, object]], httpx2.MockTransport]
STEVENBLACK = "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts"


def blocking(status: str = "enabled", timer: float | None = None) -> dict[str, object]:
    return {"blocking": status, "timer": timer, "took": 0.0001}


def group(group_id: int, name: str) -> dict[str, object]:
    return {"name": name, "comment": None, "enabled": True, "id": group_id, "date_added": 0, "date_modified": 0}


def rule(domain: str, rule_type: str, kind: str, groups: list[int]) -> dict[str, object]:
    return {
        "domain": domain,
        "unicode": domain,
        "type": rule_type,
        "kind": kind,
        "comment": None,
        "enabled": True,
        "id": 7,
        "groups": groups,
        "date_added": 1795533825,
        "date_modified": 1795533825,
    }


def subscribed(list_id: int, status: int, *, enabled: bool = True) -> dict[str, object]:
    return {
        "address": f"https://lists.example/{list_id}.txt",
        "comment": None,
        "groups": [0],
        "enabled": enabled,
        "id": list_id,
        "date_added": 1795533825,
        "date_modified": 1795533825,
        "type": "block",
        "date_updated": 1795533826 if status else 0,
        "number": 100,
        "invalid_domains": 0,
        "abp_entries": 0,
        "status": status,
    }


def query(domain: str, status: str, client: str) -> dict[str, object]:
    return {
        "id": 61,
        "time": 1795548769.58,
        "type": "A",
        "status": status,
        "dnssec": "UNKNOWN",
        "domain": domain,
        "upstream": None,
        "reply": {"type": "IP", "time": 0.0002},
        "client": {"ip": client, "name": None},
        "list_id": -3,
        "ede": {"code": -1, "text": None},
        "cname": None,
    }


def query_log(*queries: dict[str, object]) -> dict[str, object]:
    return {
        "queries": list(queries),
        "cursor": None,
        "recordsTotal": 37,
        "recordsFiltered": len(queries),
        "earliest_timestamp": 1795470600,
        "earliest_timestamp_disk": 1795548732.8,
        "took": 0.0003,
    }


def client_record(client: str, groups: list[int]) -> dict[str, object]:
    return {
        "client": client,
        "name": "",
        "comment": None,
        "groups": groups,
        "id": len(client),
        "date_added": 0,
        "date_modified": 0,
    }


def versions(ftl_remote: str = "v6.9") -> dict[str, object]:
    def component(local: str, remote: str | None) -> dict[str, object]:
        return {"local": {"version": local, "branch": "master", "hash": "abc"}, "remote": {"version": remote}}

    return {
        "version": {
            # A component the Pi-hole gives no newest release for.
            "core": {"local": {"version": "v6.6"}},
            "web": component("v6.6.1", None),
            "ftl": component("v6.9", ftl_remote),
        },
        "took": 0.0001,
    }


def padd(
    *, gravity_size: int = 81677, ram: float = 5.3, load: float = 0.5, temp: float | None = 45.0
) -> dict[str, object]:
    return {
        "recent_blocked": None,
        "active_clients": 2,
        "gravity_size": gravity_size,
        "top_domain": None,
        "top_blocked": None,
        "top_client": None,
        "blocking": "enabled",
        "queries": {"total": 27, "blocked": 2, "percent_blocked": 7.4, "query_frequency": 0},
        "cache": {"size": 10000, "inserted": 3, "evicted": 0},
        "system": {
            "uptime": 1743445,
            "memory": {
                "ram": {"total": 3886828, "free": 1597792, "used": 206776, "available": 3565128, "%used": ram},
                "swap": {"total": 0, "free": 0, "used": 0, "%used": 0},
            },
            "procs": 288,
            "cpu": {"nprocs": 4, "%cpu": 0.15, "load": {"raw": [0, 0.02, 0], "percent": [0, load, 0]}},
            "ftl": {"%mem": 0.3, "%cpu": 0.025},
        },
        "node_name": "pi.hole",
        "host_model": None,
        "config": {
            "dhcp_active": False,
            "dhcp_start": "",
            "dhcp_end": "",
            "dhcp_ipv6": False,
            "dns_domain": "lan",
            "dns_port": 53,
            "dns_num_upstreams": 2,
            "dns_dnssec": False,
            "dns_revServer_active": False,
            "privacy_level": 0,
        },
        "sensors": {"cpu_temp": temp, "hot_limit": 60, "unit": "C"},
        "took": 0.0019,
    }


def message(message_id: int, text: str) -> dict[str, object]:
    return {"id": message_id, "timestamp": 1795548000, "type": "LIST", "plain": text, "html": text}


SEARCH_BODY = {
    "search": {
        "domains": [rule("(\\.|^)doubleclick\\.net$", "deny", "regex", [2])],
        "gravity": [
            {
                "domain": "doubleclick.net",
                "type": "block",
                "address": STEVENBLACK,
                "comment": None,
                "enabled": True,
                "id": 1,
                "groups": [0],
            }
        ],
        "results": {"domains": {"exact": 0, "regex": 1}, "gravity": {"allow": 0, "block": 1}, "total": 2},
    },
    "took": 0.0025,
}
GROUPS_BODY = {"groups": [group(0, "Default"), group(2, "Kids"), group(3, "Unused")], "took": 0.0002}
DEVICES_BODY = {
    "devices": [
        {
            "id": 3,
            "hwaddr": "12:34:56:78:9a:bc",
            "interface": "eth0",
            "firstSeen": 1795548732,
            "lastQuery": 1795554000,
            "numQueries": 29,
            "macVendor": "Raspberry Pi Trading Ltd",
            "ips": [
                {"ip": "192.168.1.20", "name": "nas.lan", "lastSeen": 1795557180, "nameUpdated": 1795557180},
                {"ip": "fd00::20", "name": None, "lastSeen": 1795557180, "nameUpdated": 0},
            ],
        }
    ],
    "took": 0.0013,
}


def test_explain_domain_gathers_matches_their_groups_and_recent_queries(
    route: Route, sent: list[httpx2.Request]
) -> None:
    bodies = {
        "/api/dns/blocking": blocking(),
        "/api/search/doubleclick.net": SEARCH_BODY,
        "/api/groups": GROUPS_BODY,
        "/api/queries": query_log(query("doubleclick.net", "GRAVITY", "192.168.1.235")),
    }
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=route(bodies)) as api:
        explanation = api.explain_domain("doubleclick.net", recent=5)

    assert (explanation.domain, explanation.blocking) == ("doubleclick.net", "enabled")
    assert [(r.type, r.kind) for r in explanation.rules] == [("deny", "regex")]
    assert [item.address for item in explanation.lists] == [STEVENBLACK]
    # Only the groups the matches refer to.
    assert explanation.groups == {0: "Default", 2: "Kids"}
    assert [(q.status, q.client.ip) for q in explanation.recent_queries] == [("GRAVITY", "192.168.1.235")]
    log_request = next(request for request in sent if request.url.path == "/api/queries")
    assert dict(log_request.url.params) == {"domain": "doubleclick.net", "length": "5", "disk": "false", "start": "0"}


def test_explain_client_finds_the_device_and_ranks_records_as_pi_hole_tries_them(
    route: Route, sent: list[httpx2.Request]
) -> None:
    records = [
        client_record(":eth0", [3]),
        client_record("nas.lan", [2]),
        client_record("12:34:56:78:9A:BC", [2]),
        client_record("fd00::/64", [0]),
        client_record("fd00:0::20", [2]),
        client_record("192.168.1.99", [3]),
        # Not a subnet Pi-hole could hold: skipped, not fatal.
        client_record("fd00::/999", [3]),
    ]
    bodies = {
        "/api/network/devices": DEVICES_BODY,
        "/api/clients": {"clients": records, "took": 0.0002},
        "/api/groups": GROUPS_BODY,
        "/api/queries": query_log(query("example.com", "FORWARDED", "fd00::20")),
    }
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=route(bodies)) as api:
        explanation = api.explain_client("fd00::20")

    assert explanation.device is not None and explanation.device.mac_vendor == "Raspberry Pi Trading Ltd"
    # IP address, subnet, MAC address (in any case), hostname, interface; not
    # another device's address.
    assert [record.client for record in explanation.clients] == [
        "fd00:0::20",
        "fd00::/64",
        "12:34:56:78:9A:BC",
        "nas.lan",
        ":eth0",
    ]
    assert explanation.groups == {0: "Default", 2: "Kids", 3: "Unused"}
    devices_request = next(request for request in sent if request.url.path == "/api/network/devices")
    log_request = next(request for request in sent if request.url.path == "/api/queries")
    assert dict(devices_request.url.params) == {"max_devices": "1000", "max_addresses": "100"}
    assert dict(log_request.url.params) == {"client_ip": "fd00::20", "length": "10", "disk": "false", "start": "0"}


def test_explain_client_of_an_address_the_pi_hole_has_not_seen_has_no_device(route: Route) -> None:
    bodies = {
        "/api/network/devices": DEVICES_BODY,
        "/api/clients": {"clients": [client_record("12:34:56:78:9A:BC", [2])], "took": 0.0002},
        "/api/groups": GROUPS_BODY,
        "/api/queries": query_log(),
    }
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=route(bodies)) as api:
        explanation = api.explain_client("192.168.1.77")

    assert (explanation.device, explanation.clients, explanation.groups) == (None, [], {})


def test_explain_client_refuses_an_address_that_is_not_an_ip_address(route: Route, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=route({})) as api:
        with pytest.raises(ArgumentError, match="isn't an IP address") as error:
            api.explain_client("laptop.lan")

    assert (error.value.parameter, sent) == ("address", [])


def health_bodies(**overrides: object) -> dict[str, object]:
    return {
        "/api/dns/blocking": blocking(),
        "/api/info/messages": {"messages": [], "took": 0.0001},
        "/api/info/version": versions(),
        "/api/lists": {"lists": [subscribed(1, 2)], "took": 0.0003},
        "/api/padd": padd(),
    } | overrides


def test_check_health_lists_each_problem_most_urgent_first(route: Route) -> None:
    bodies = health_bodies(
        **{
            "/api/dns/blocking": blocking("disabled", timer=29.6),
            "/api/info/messages": {"messages": [message(1, "List 3 failed"), message(2, "Rate-limiting")], "took": 0.1},
            "/api/info/version": versions(ftl_remote="v6.10"),
            "/api/lists": {
                "lists": [
                    subscribed(1, 2),
                    subscribed(2, 4),
                    subscribed(3, 3),
                    subscribed(4, 3),
                    subscribed(5, 0),
                    subscribed(6, 4, enabled=False),
                ],
                "took": 0.0003,
            },
            "/api/padd": padd(gravity_size=0, ram=93.4, load=150.0, temp=61.2),
        }
    )
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=route(bodies)) as api:
        report = api.check_health()

    assert report.findings == [
        "Blocking is disabled, so every domain gets through: it resumes in 30 seconds.",
        "The blocklists hold no domains: add a list, or run a gravity update.",
        "1 enabled list couldn't be downloaded and have no copy, so their domains aren't in effect.",
        "The Pi-hole reported 2 problems, in `messages`.",
        "The CPU is at 61°C, at or above the 60°C limit.",
        "RAM is 93% used.",
        "The 5-minute load is 150% of the CPU's cores.",
        "2 enabled lists couldn't be downloaded in the last gravity update, so an older copy is in use.",
        "1 enabled list hasn't been downloaded yet: run a gravity update.",
        "An update is available for FTL: v6.9 to v6.10.",
    ]
    assert [(u.component, u.installed, u.available) for u in report.updates] == [("ftl", "v6.9", "v6.10")]
    assert [item.id for item in report.problem_lists] == [2, 3, 4, 5]
    assert report.blocking_timer == 29.6


@pytest.mark.parametrize(
    ("status", "finding"),
    [
        ("failure", "The DNS server isn't running, so the Pi-hole answers no queries."),
        ("unknown", "The blocking status isn't known yet, as while the Pi-hole starts."),
        ("disabled", "Blocking is disabled, so every domain gets through."),
    ],
)
def test_check_health_names_each_blocking_problem(status: str, finding: str, route: Route) -> None:
    with PiHole(
        BASE_URL, auth=PiHoleAuth(PASSWORD), transport=route(health_bodies(**{"/api/dns/blocking": blocking(status)}))
    ) as api:
        assert api.check_health().findings == [finding]


@pytest.mark.anyio
async def test_async_insights_send_the_same_requests(route: Route, sent: list[httpx2.Request]) -> None:
    bodies = health_bodies(
        **{
            "/api/search/doubleclick.net": SEARCH_BODY,
            "/api/groups": GROUPS_BODY,
            "/api/queries": query_log(),
            "/api/network/devices": DEVICES_BODY,
            "/api/clients": {"clients": [], "took": 0.0002},
        }
    )
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=route(bodies)) as api:
        explanation = await api.explain_domain("doubleclick.net")
        client = await api.explain_client("192.168.1.20")
        report = await api.check_health()

    assert (len(explanation.lists), client.device is not None, report.findings) == (1, True, [])
    assert [request.url.path for request in sent] == [
        "/api/dns/blocking",
        "/api/search/doubleclick.net",
        "/api/groups",
        "/api/queries",
        "/api/network/devices",
        "/api/clients",
        "/api/groups",
        "/api/queries",
        "/api/dns/blocking",
        "/api/info/messages",
        "/api/info/version",
        "/api/lists",
        "/api/padd",
    ]
    with pytest.raises(ArgumentError):
        await api.explain_client("not an address")


def test_ai_tools_list_the_insights_as_read_only_tools_tagged_insights() -> None:
    tools: dict[str, Any] = {tool.name: tool for tool in list_tools(PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD)))}

    assert {
        name: (tools[name].read_only, tools[name].tags) for name in ("explain_domain", "explain_client", "check_health")
    } == {
        "explain_domain": (True, ("insights",)),
        "explain_client": (True, ("insights",)),
        "check_health": (True, ("insights",)),
    }
