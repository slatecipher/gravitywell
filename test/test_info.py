from collections.abc import Callable
from datetime import UTC, datetime

import httpx2
import pytest
from clientx.tools import ToolError, list_tools

from gravitywell import AsyncPiHole, PiHole, PiHoleAuth
from gravitywell.models import SystemInfoResponse, VersionResponse

BASE_URL = "http://pi.hole"
PASSWORD = "app-password"
# conftest.py's `serve` fixture.
type Serve = Callable[[object], httpx2.MockTransport]

# The spec's example, with a different version per component so a mix-up shows,
# and the fields gravitywell doesn't model.
VERSION_BODY = {
    "version": {
        "core": {
            "local": {"branch": "master", "version": "v6.1", "hash": "955e36a9"},
            "remote": {"version": "v6.1", "hash": "955e36a9"},
        },
        "web": {
            "local": {"branch": "master", "version": "v6.2", "hash": "f69f7e88"},
            "remote": {"version": "v6.2", "hash": "f69f7e88"},
        },
        "ftl": {
            "local": {"branch": "master", "version": "v6.3", "hash": "64441ed6", "date": "2025-11-01 20:25:24 +0100"},
            "remote": {"version": "v6.3", "hash": "64441ed6"},
        },
        "docker": {"local": None, "remote": None},
    },
    "took": 0.0003,
}


def installed(body: VersionResponse) -> tuple[str | None, str | None, str | None]:
    versions = body.version
    return versions.core.local.version, versions.web.local.version, versions.ftl.local.version


def test_version_gets_info_version_and_reads_the_installed_versions(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(VERSION_BODY)) as api:
        assert installed(api.info.version()) == ("v6.1", "v6.2", "v6.3")

    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/info/version")


@pytest.mark.anyio
async def test_async_version_gets_info_version_and_reads_the_installed_versions(
    serve: Serve, sent: list[httpx2.Request]
) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(VERSION_BODY)) as api:
        assert installed(await api.info.version()) == ("v6.1", "v6.2", "v6.3")

    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/info/version")


# The live test Pi-hole's answers, cut short.
SYSTEM_BODY = {
    "system": {
        "uptime": 1736161,
        "memory": {
            "ram": {"total": 3886828, "free": 1605136, "used": 206252, "available": 3582040, "%used": 5.3},
            "swap": {"total": 2097148, "free": 2097148, "used": 0, "%used": 0},
        },
        "procs": 289,
        "cpu": {"nprocs": 4, "%cpu": 0.05, "load": {"raw": [0.05, 0.03, 0], "percent": [1.25, 0.75, 0]}},
        "ftl": {"%mem": 0.31, "%cpu": 0.025},
    },
    "took": 0.0002,
}
HOST_BODY = {
    "host": {
        "uname": {
            "domainname": "(none)",
            "machine": "aarch64",
            "nodename": "119c5d57dcb0",
            "release": "6.18.50+rpt-rpi-v8",
            "sysname": "Linux",
            "version": "#1 SMP PREEMPT Debian 1:6.18.50-1+rpt1 (2026-09-11)",
        },
        "model": None,
        "dmi": {"bios": {"vendor": None}},
    },
    "took": 0.0002,
}
SENSORS_BODY = {
    "sensors": {
        "list": [
            {"name": "pwmfan", "path": "hwmon2", "source": "devices/platform/pwm-fan", "temps": []},
            {
                "name": "cpu_thermal",
                "path": "hwmon0",
                "source": "devices/virtual/thermal/thermal_zone0",
                "temps": [{"name": None, "value": 45.764, "max": None, "crit": None, "sensor": "temp1"}],
            },
        ],
        "cpu_temp": 45.764,
        "hot_limit": 60,
        "unit": "C",
    },
    "took": 0.0002,
}
ALLOW_DENY = {"allowed": {"total": 0, "enabled": 0}, "denied": {"total": 2, "enabled": 1}}
FTL_BODY = {
    "ftl": {
        "database": {
            "gravity": 81677,
            "antigravity": 0,
            "groups": 1,
            "lists": 1,
            "clients": 0,
            "domains": ALLOW_DENY,
            "regex": ALLOW_DENY,
        },
        "privacy_level": 0,
        "query_frequency": 0,
        "clients": {"total": 2, "active": 2},
        "pid": 187,
        "uptime": 11823660.206433,
        "%mem": 0.31,
        "%cpu": 0.025,
        "allow_destructive": True,
        "dnsmasq": {"dns_cache_inserted": 94},
    },
    "took": 0.0002,
}
DATABASE_BODY = {
    "size": 90112,
    "type": "Regular file",
    "queries": 51,
    "earliest_timestamp": 1795459200,
    "queries_disk": 51,
    "earliest_timestamp_disk": 0,
    "sqlite_version": "3.54.1",
    "took": 0.0002,
}
DHCP = {
    "ack": 0,
    "decline": 0,
    "discover": 0,
    "inform": 0,
    "nak": 0,
    "offer": 0,
    "release": 0,
    "request": 0,
    "noanswer": 0,
    "bootp": 0,
    "pxe": 0,
    "leases": {"allocated_4": 0, "pruned_4": 0, "allocated_6": 0, "pruned_6": 0},
}
METRICS_BODY = {
    "metrics": {
        "dns": {
            "cache": {
                "size": 10000,
                "inserted": 94,
                "evicted": 0,
                "expired": 85,
                "immortal": 14,
                "content": [{"type": 1, "name": "A", "count": {"valid": 3, "stale": 10}}],
            },
            "replies": {"local": 408, "forwarded": 29, "optimized": 2, "unanswered": 0, "auth": 0, "sum": 439},
        },
        "dhcp": DHCP,
    },
    "took": 0.0002,
}


def test_system_reads_memory_cpu_and_ftls_share(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(SYSTEM_BODY)) as api:
        system = api.info.system().system

    assert (system.uptime, system.memory.ram.total, system.memory.ram.percent_used) == (1736161, 3886828, 5.3)
    assert (system.cpu.nprocs, system.cpu.load.percent, system.ftl.percent_mem) == (4, [1.25, 0.75, 0], 0.31)
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/info/system")


@pytest.mark.anyio
async def test_async_host_reads_the_operating_system(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(HOST_BODY)) as api:
        host = (await api.info.host()).host

    assert (host.uname.sysname, host.uname.machine, host.model) == ("Linux", "aarch64", None)
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/info/host")


def test_sensors_reads_the_list_and_cpu_temperature(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(SENSORS_BODY)) as api:
        sensors = api.info.sensors().sensors

    assert [(sensor.name, len(sensor.temps)) for sensor in sensors.sensors] == [("pwmfan", 0), ("cpu_thermal", 1)]
    assert (sensors.cpu_temp, sensors.hot_limit, sensors.unit) == (45.764, 60, "C")
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/info/sensors")


@pytest.mark.anyio
async def test_async_ftl_reads_database_counts_and_settings(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(FTL_BODY)) as api:
        ftl = (await api.info.ftl()).ftl

    assert (ftl.database.gravity, ftl.database.domains.denied.enabled, ftl.privacy_level) == (81677, 1, 0)
    assert (ftl.uptime, ftl.percent_cpu, ftl.allow_destructive) == (11823660.206433, 0.025, True)
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/info/ftl")


def test_database_reads_an_unknown_earliest_timestamp_as_none(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(DATABASE_BODY)) as api:
        database = api.info.database()

    assert (database.size, database.queries, database.sqlite_version) == (90112, 51, "3.54.1")
    assert (database.earliest_timestamp, database.earliest_timestamp_disk) == (
        datetime.fromtimestamp(1795459200, tz=UTC),
        None,
    )
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/info/database")


@pytest.mark.anyio
async def test_async_metrics_reads_the_dns_cache_and_replies(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(METRICS_BODY)) as api:
        metrics = (await api.info.metrics()).metrics

    assert (metrics.dns.cache.size, metrics.dns.cache.content[0].count.stale) == (10000, 10)
    assert (metrics.dns.replies.local, metrics.dns.replies.sum, metrics.dhcp.leases.allocated_4) == (408, 439, 0)
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/info/metrics")


def test_models_with_percent_names_read_back_the_same_from_their_dumps() -> None:
    system = SystemInfoResponse.model_validate(SYSTEM_BODY)

    assert SystemInfoResponse.model_validate(system.model_dump(mode="json")) == system
    assert SystemInfoResponse.model_validate(system.model_dump(mode="json", by_alias=True)) == system


# A diagnosis message the live test Pi-hole reported.
MESSAGES_BODY = {
    "messages": [
        {
            "id": 1,
            "timestamp": 1795546369.5,
            "type": "SUBNET",
            "plain": "Client 192.168.1.235 is managed by 2 groups (IDs 11,12), all describing the same subnet.",
            "html": "Client <code>192.168.1.235</code> is managed by 2 groups.",
        }
    ],
    "took": 0.0003,
}


def test_messages_reads_the_diagnosis_messages(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(MESSAGES_BODY)) as api:
        [message] = api.info.messages().messages

    assert (message.id, message.type, message.timestamp) == (1, "SUBNET", datetime.fromtimestamp(1795546369.5, tz=UTC))
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/info/messages")


@pytest.mark.anyio
async def test_async_message_count_gets_the_count(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve({"count": 1, "took": 0.0001})) as api:
        assert (await api.info.message_count()).count == 1

    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/info/messages/count")


def test_delete_messages_joins_the_ids_into_one_path_segment(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve({})) as api:
        api.info.delete_messages([3, 4])

    [request] = sent
    assert (request.method, request.url.path) == ("DELETE", "/api/info/messages/3,4")


@pytest.mark.anyio
async def test_async_delete_messages_deletes_one_message(serve: Serve, sent: list[httpx2.Request]) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve({})) as api:
        await api.info.delete_messages([1])

    [request] = sent
    assert (request.method, request.url.path) == ("DELETE", "/api/info/messages/1")


def test_ai_tools_need_at_least_one_message_id_to_delete() -> None:
    tools = {tool.name: tool for tool in list_tools(PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD)))}

    with pytest.raises(ToolError, match="at least 1 item"):
        tools["info_delete_messages"].call({"ids": []})
    assert (tools["info_delete_messages"].destructive, tools["info_delete_messages"].idempotent) == (True, True)
    assert "info__delete_messages" not in tools
