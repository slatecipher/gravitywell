from collections.abc import Callable

import httpx2
import pytest

from gravitywell import AsyncPiHole, PiHole, PiHoleAuth

BASE_URL = "http://pi.hole"
PASSWORD = "app-password"
# conftest.py's `serve` fixture.
type Serve = Callable[[object], httpx2.MockTransport]

# The test Pi-hole's summary, cut short.
SUMMARY_BODY: dict[str, object] = {
    "recent_blocked": "ads.google.com",
    "active_clients": 2,
    "gravity_size": 81677,
    "top_domain": "example.com",
    "top_blocked": "doubleclick.net",
    "top_client": "localhost",
    "blocking": "enabled",
    "queries": {"total": 27, "blocked": 2, "percent_blocked": 7.4, "query_frequency": 0},
    "cache": {"size": 10000, "inserted": 3, "evicted": 0},
    "system": {
        "uptime": 1743445,
        "memory": {
            "ram": {"total": 3886828, "free": 1597792, "used": 206776, "available": 3565128, "%used": 5.3},
            "swap": {"total": 2097148, "free": 2097148, "used": 0, "%used": 0},
        },
        "procs": 288,
        "cpu": {"nprocs": 4, "%cpu": 0.15, "load": {"raw": [0, 0.02, 0], "percent": [0, 0.5, 0]}},
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
        "dns_revServer_active": True,
        "privacy_level": 0,
    },
    "sensors": {"cpu_temp": 45.7, "hot_limit": 60, "unit": "C"},
    "took": 0.0019,
}
FULL_BODY = SUMMARY_BODY | {
    "iface": {
        "v4": {
            "addr": "172.18.0.2",
            "rx_bytes": {"value": 5.2, "unit": "M"},
            "tx_bytes": {"value": 12.4, "unit": "M"},
            "num_addrs": 1,
            "name": "eth0",
            "gw_addr": "172.18.0.1",
        },
        "v6": {"addr": None, "num_addrs": 0, "name": "eth0", "gw_addr": None},
    },
    "version": {
        "core": {"local": {"version": "v6.6", "branch": "master", "hash": "f7c0220e"}, "remote": {"version": "v6.6"}},
        "web": {
            "local": {"version": "v6.6.1", "branch": "master", "hash": "fb699c4e"},
            "remote": {"version": "v6.6.1"},
        },
        "ftl": {"local": {"version": "v6.9", "branch": "master", "hash": "2a0fcb74"}, "remote": {"version": "v6.9"}},
        "docker": {"local": "2026.11.0", "remote": "2026.11.0"},
    },
}


def test_summary_reads_the_state_without_interfaces_or_versions(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(SUMMARY_BODY)) as api:
        summary = api.padd.summary()

    assert (summary.blocking, summary.queries.total, summary.top_blocked, summary.sensors.cpu_temp) == (
        "enabled",
        27,
        "doubleclick.net",
        45.7,
    )
    assert (summary.config.dns_rev_server_active, summary.system.cpu.load.percent) == (True, [0, 0.5, 0])
    assert (summary.iface, summary.version) == (None, None)
    [request] = sent
    assert (request.method, request.url.path, dict(request.url.params)) == ("GET", "/api/padd", {"full": "false"})


@pytest.mark.anyio
async def test_async_full_summary_adds_interfaces_and_versions(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(FULL_BODY)) as api:
        summary = await api.padd.summary(full=True)

    assert summary.iface is not None and summary.version is not None
    assert (summary.iface.v4.gw_addr, summary.iface.v6.addr, summary.version.ftl.local.version) == (
        "172.18.0.1",
        None,
        "v6.9",
    )
    [request] = sent
    assert dict(request.url.params) == {"full": "true"}
