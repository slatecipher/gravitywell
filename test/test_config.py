from collections.abc import Callable

import httpx2
import pytest
from clientx import ArgumentError
from clientx.tools import list_tools

from gravitywell import AsyncPiHole, PiHole, PiHoleAuth

BASE_URL = "http://pi.hole"
PASSWORD = "app-password"
# conftest.py's `serve` fixture.
type Serve = Callable[[object], httpx2.MockTransport]


def config_body(
    hosts: list[str] | None = None, cname_records: list[str] | None = None, upstreams: list[str] | None = None
) -> dict[str, object]:
    # A `PATCH` answers with the whole config, which holds more than `dns`.
    dns = {"hosts": hosts or [], "cnameRecords": cname_records or [], "upstreams": upstreams or ["9.9.9.9"]}
    return {"config": {"dns": dns, "webserver": {"api": {"app_sudo": True}}}, "took": 0.0002}


def test_dns_records_reads_each_entry_as_an_ip_and_its_hostnames(serve: Serve, sent: list[httpx2.Request]) -> None:
    # Entries as Pi-hole allows them: tabs and comments, and several names.
    body = config_body(hosts=["192.168.1.10 nas.lan", "192.168.1.11\tprinter.lan printer # office"])
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(body)) as api:
        response = api.config.dns_records()

    assert [(record.ip, record.hostnames) for record in response.records] == [
        ("192.168.1.10", ["nas.lan"]),
        ("192.168.1.11", ["printer.lan", "printer"]),
    ]
    assert response.took == 0.0002
    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/config/dns/hosts")


@pytest.mark.anyio
async def test_cname_records_read_aliases_target_and_ttl(serve: Serve, sent: list[httpx2.Request]) -> None:
    body = config_body(cname_records=["files.lan,nas.lan", "a.lan,b.lan,nas.lan,300"])
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(body)) as api:
        records = (await api.config.cname_records()).records

    assert [(record.domains, record.target, record.ttl) for record in records] == [
        (["files.lan"], "nas.lan", None),
        (["a.lan", "b.lan"], "nas.lan", 300),
    ]
    [request] = sent
    assert request.url.path == "/api/config/dns/cnameRecords"


def test_upstreams_reads_the_servers(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(config_body(upstreams=["127.0.0.1#5335"]))) as api:
        assert api.config.upstreams().servers == ["127.0.0.1#5335"]

    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/config/dns/upstreams")


def test_add_dns_record_puts_ip_and_hostname_as_one_entry(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve({})) as api:
        api.config.add_dns_record("192.168.1.10", "nas.lan")

    [request] = sent
    assert (request.method, request.url.path) == ("PUT", "/api/config/dns/hosts/192.168.1.10 nas.lan")


def test_add_cname_record_adds_the_ttl_only_when_given(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve({})) as api:
        api.config.add_cname_record("files.lan", "nas.lan")
        api.config.add_cname_record("media.lan", "nas.lan", ttl=300)

    assert [(request.method, request.url.path) for request in sent] == [
        ("PUT", "/api/config/dns/cnameRecords/files.lan,nas.lan"),
        ("PUT", "/api/config/dns/cnameRecords/media.lan,nas.lan,300"),
    ]


def test_a_delete_sends_the_stored_entry_which_pi_hole_matches_exactly(
    serve: Serve, sent: list[httpx2.Request]
) -> None:
    body = config_body(hosts=["192.168.1.10   nas.lan # NAS"], cname_records=["files.lan,nas.lan,300"])
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(body)) as api:
        api.config.delete_dns_record("192.168.1.10", "NAS.lan")
        api.config.delete_cname_record("files.lan", "nas.lan")

    assert [(request.method, request.url.path) for request in sent] == [
        ("GET", "/api/config/dns/hosts"),
        ("DELETE", "/api/config/dns/hosts/192.168.1.10   nas.lan # NAS"),
        ("GET", "/api/config/dns/cnameRecords"),
        ("DELETE", "/api/config/dns/cnameRecords/files.lan,nas.lan,300"),
    ]


def test_set_upstreams_patches_them_and_reads_back_the_servers(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(config_body(upstreams=["9.9.9.9"]))) as api:
        assert api.config.set_upstreams(["9.9.9.9"]).servers == ["9.9.9.9"]

    [request] = sent
    assert (request.method, request.url.path) == ("PATCH", "/api/config")
    assert request.content == b'{"config":{"dns":{"upstreams":["9.9.9.9"]}}}'


@pytest.mark.anyio
async def test_async_writes_send_the_same_requests(serve: Serve, sent: list[httpx2.Request]) -> None:
    body = config_body(hosts=["192.168.1.10 nas.lan"], cname_records=["files.lan,nas.lan"])
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(body)) as api:
        await api.config.add_dns_record("192.168.1.10", "nas.lan")
        await api.config.delete_dns_record("192.168.1.10", "nas.lan")
        await api.config.add_cname_record("files.lan", "nas.lan")
        await api.config.delete_cname_record("files.lan", "nas.lan")
        assert (await api.config.set_upstreams(["9.9.9.9"])).servers == ["9.9.9.9"]

    assert [request.method for request in sent] == ["PUT", "GET", "DELETE", "PUT", "GET", "DELETE", "PATCH"]


def test_deleting_a_record_that_does_not_exist_is_refused(serve: Serve, sent: list[httpx2.Request]) -> None:
    body = config_body(hosts=["192.168.1.11 nas.lan"], cname_records=["files.lan,printer.lan"])
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(body)) as api:
        with pytest.raises(ArgumentError, match="No local DNS record") as record:
            api.config.delete_dns_record("192.168.1.10", "nas.lan")
        with pytest.raises(ArgumentError, match="No local CNAME record") as cname:
            api.config.delete_cname_record("files.lan", "nas.lan")

    assert (record.value.parameter, cname.value.parameter) == ("hostname", "domain")
    assert [request.method for request in sent] == ["GET", "GET"]


def test_deleting_one_name_of_a_record_that_names_others_is_refused(serve: Serve, sent: list[httpx2.Request]) -> None:
    body = config_body(hosts=["192.168.1.10 nas.lan nas"], cname_records=["files.lan,media.lan,nas.lan"])
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(body)) as api:
        with pytest.raises(ArgumentError, match="names other hostnames too"):
            api.config.delete_dns_record("192.168.1.10", "nas")
        with pytest.raises(ArgumentError, match="names other aliases too"):
            api.config.delete_cname_record("files.lan", "nas.lan")

    assert [request.method for request in sent] == ["GET", "GET"]


@pytest.mark.parametrize(
    ("ip", "hostname", "parameter"),
    [("192.168.1.10", "nas.lan nas", "hostname"), ("192.168.1.10", "nas.lan,x", "hostname"), ("", "nas.lan", "ip")],
)
def test_a_name_that_would_split_an_entry_is_refused(
    ip: str, hostname: str, parameter: str, serve: Serve, sent: list[httpx2.Request]
) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve({})) as api:
        with pytest.raises(ArgumentError) as dns:
            api.config.add_dns_record(ip, hostname)
        with pytest.raises(ArgumentError) as cname:
            api.config.add_cname_record("files.lan", "nas.lan #x")

    assert (dns.value.parameter, cname.value.parameter) == (parameter, "target")
    assert sent == []


def test_an_empty_upstream_list_is_refused(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve({})) as api:
        with pytest.raises(ArgumentError, match="name at least one server") as error:
            api.config.set_upstreams([])

    assert error.value.parameter == "servers"
    assert sent == []


def test_ai_tools_mark_only_the_deletes_and_set_upstreams_destructive() -> None:
    tools = {tool.name: tool for tool in list_tools(PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD)))}
    config = {name: (tool.read_only, tool.destructive) for name, tool in tools.items() if name.startswith("config")}

    assert config == {
        "config_dns_records": (True, False),
        "config_add_dns_record": (False, False),
        "config_delete_dns_record": (False, True),
        "config_cname_records": (True, False),
        "config_add_cname_record": (False, False),
        "config_delete_cname_record": (False, True),
        "config_upstreams": (True, False),
        "config_set_upstreams": (False, True),
    }
