from collections.abc import Callable
from datetime import UTC, datetime

import httpx2
import pytest

from gravitywell import AsyncPiHole, PiHole, PiHoleAuth

BASE_URL = "http://pi.hole"
PASSWORD = "app-password"
# conftest.py's `serve` fixture.
type Serve = Callable[[object], httpx2.MockTransport]

# Leases as FTL reads them from dnsmasq's lease file: `*` for a missing
# hostname or client ID, and an expiry of 0 for a lease that never ends.
LEASES_BODY = {
    "leases": [
        {"expires": 1795550000, "name": "laptop", "hwaddr": "12:34:56:78:9a:bc", "ip": "192.168.1.50", "clientid": "*"},
        {"expires": 0, "name": "*", "hwaddr": "12:34:56:78:9a:bd", "ip": "192.168.1.51", "clientid": "01:12"},
    ],
    "took": 0.0002,
}


def test_leases_reads_a_lease_that_never_ends_as_none(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(LEASES_BODY)) as api:
        leases = api.dhcp.leases().leases

    assert [(lease.ip, lease.name, lease.expires) for lease in leases] == [
        ("192.168.1.50", "laptop", datetime.fromtimestamp(1795550000, tz=UTC)),
        ("192.168.1.51", "*", None),
    ]
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/dhcp/leases")


@pytest.mark.anyio
async def test_async_delete_lease_deletes_by_ip_address(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve({})) as api:
        await api.dhcp.delete_lease("192.168.1.50")

    [request] = sent
    assert (request.method, request.url.path) == ("DELETE", "/api/dhcp/leases/192.168.1.50")


@pytest.mark.anyio
async def test_async_leases_gets_dhcp_leases(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(LEASES_BODY)) as api:
        assert len((await api.dhcp.leases()).leases) == 2

    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/dhcp/leases")


def test_delete_lease_deletes_by_ip_address(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve({})) as api:
        api.dhcp.delete_lease("192.168.1.51")

    [request] = sent
    assert (request.method, request.url.path) == ("DELETE", "/api/dhcp/leases/192.168.1.51")
