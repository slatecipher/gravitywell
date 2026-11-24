from collections.abc import Callable
from datetime import UTC, datetime

import httpx2
import pytest

from gravitywell import AsyncPiHole, PiHole, PiHoleAuth

BASE_URL = "http://pi.hole"
PASSWORD = "app-password"
# conftest.py's `serve` fixture.
type Serve = Callable[[object], httpx2.MockTransport]

# The live test Pi-hole's answers, cut short.
DEVICES_BODY = {
    "devices": [
        {
            "id": 3,
            "hwaddr": "ip-192.168.1.235",
            "interface": "eth0",
            "firstSeen": 1795540100,
            "lastQuery": 1795546369,
            "numQueries": 44,
            "macVendor": "",
            "ips": [{"ip": "192.168.1.235", "name": None, "lastSeen": 1795546680, "nameUpdated": 0}],
        },
        {
            "id": 2,
            "hwaddr": "0e:18:ee:8b:97:9b",
            "interface": "eth0",
            "firstSeen": 1795533840,
            "lastQuery": 0,
            "numQueries": 0,
            "macVendor": "",
            "ips": [{"ip": "172.18.0.2", "name": None, "lastSeen": 1795546680, "nameUpdated": 0}],
        },
    ],
    "took": 0.002,
}
GATEWAY_BODY = {
    "gateway": [{"family": "inet", "interface": "eth0", "address": "172.18.0.1", "local": ["172.18.0.2"]}],
    "took": 0.0003,
}
INTERFACES_BODY = {
    "interfaces": [
        {
            "name": "eth0",
            "speed": 10000,
            "type": "ether",
            "flags": ["up", "broadcast", "running", "multicast", "lower_up"],
            "state": "up",
            "carrier": True,
            "proto_down": False,
            "address": "0e:18:ee:8b:97:9b",
            "broadcast": "ff:ff:ff:ff:ff:ff",
            "stats": {"rx_bytes": {"value": 4.66, "unit": "M"}, "tx_bytes": {"value": 10.16, "unit": "M"}, "bits": 64},
            "addresses": [
                {"family": "inet", "scope": "universe", "flags": [], "prefixlen": 16, "address": "172.18.0.2"},
            ],
        }
    ],
    "took": 0.0005,
}
ROUTES_BODY = {
    "routes": [
        {
            "table": 254,
            "family": "inet",
            "protocol": "boot",
            "scope": "universe",
            "type": "unicast",
            "flags": [],
            "gateway": "172.18.0.1",
            "oif": "eth0",
            "dst": "default",
        },
        {
            "table": 254,
            "family": "inet",
            "protocol": "kernel",
            "scope": "link",
            "type": "unicast",
            "flags": [],
            "dst": "172.18.0.0",
            "prefsrc": "172.18.0.2",
            "oif": "eth0",
        },
    ],
    "took": 0.0004,
}


def test_devices_reads_devices_and_sends_the_limits(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(DEVICES_BODY)) as api:
        devices = api.network.devices().devices

    assert [(device.id, device.hwaddr, device.num_queries) for device in devices] == [
        (3, "ip-192.168.1.235", 44),
        (2, "0e:18:ee:8b:97:9b", 0),
    ]
    assert (devices[0].last_query, devices[1].last_query) == (datetime.fromtimestamp(1795546369, tz=UTC), None)
    assert devices[0].ips[0].name_updated is None
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/network/devices")
    assert dict(request.url.params) == {"max_devices": "10", "max_addresses": "3"}


@pytest.mark.anyio
async def test_async_delete_device_deletes_by_id(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve({})) as api:
        await api.network.delete_device(3)

    [request] = sent
    assert (request.method, request.url.path) == ("DELETE", "/api/network/devices/3")


@pytest.mark.anyio
async def test_async_gateway_reads_the_default_route(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(GATEWAY_BODY)) as api:
        [gateway] = (await api.network.gateway()).gateway

    assert (gateway.address, gateway.interface, gateway.local) == ("172.18.0.1", "eth0", ["172.18.0.2"])
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/network/gateway")


def test_interfaces_reads_state_addresses_and_traffic(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(INTERFACES_BODY)) as api:
        [interface] = api.network.interfaces().interfaces

    assert (interface.name, interface.state, interface.speed, interface.addresses[0].prefixlen) == (
        "eth0",
        "up",
        10000,
        16,
    )
    assert (interface.stats.rx_bytes.value, interface.stats.rx_bytes.unit) == (4.66, "M")
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/network/interfaces")


@pytest.mark.anyio
async def test_async_routes_reads_routes_with_and_without_a_gateway(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(ROUTES_BODY)) as api:
        routes = (await api.network.routes()).routes

    assert [(route.dst, route.gateway, route.prefsrc) for route in routes] == [
        ("default", "172.18.0.1", None),
        ("172.18.0.0", None, "172.18.0.2"),
    ]
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/network/routes")
