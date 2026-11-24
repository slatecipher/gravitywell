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


def setting(value: object, allowed: object = None, *, restarts: bool = False, env: bool = False) -> dict[str, object]:
    return {
        "description": "What it does.",
        "allowed": allowed,
        "type": "boolean" if isinstance(value, bool) else "enum (string)",
        "value": value,
        "default": value,
        "modified": False,
        "flags": {"restart_dnsmasq": restarts, "session_reset": False, "env_var": env},
    }


# A detailed read of `dns.blocking`, as FTL nests it under its topic.
BLOCKING_BODY = {
    "config": {
        "dns": {
            "blocking": {
                "active": setting(True),
                "mode": setting("NULL", [{"item": "NULL", "description": "Answer 0.0.0.0."}], restarts=True),
            }
        }
    },
    "topics": [],
    "took": 0.0003,
}


def test_settings_flattens_a_topic_into_settings_with_dotted_keys(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(BLOCKING_BODY)) as api:
        settings = api.config.settings("dns.blocking").settings

    assert [(s.key, s.value, s.restarts_ftl, s.set_by_environment) for s in settings] == [
        ("dns.blocking.active", True, False, False),
        ("dns.blocking.mode", "NULL", True, False),
    ]
    assert settings[1].allowed is not None and not isinstance(settings[1].allowed, str)
    assert [(allowed.item, allowed.description) for allowed in settings[1].allowed] == [("NULL", "Answer 0.0.0.0.")]
    [request] = sent
    assert (request.method, request.url.path, dict(request.url.params)) == (
        "GET",
        "/api/config/dns/blocking",
        {"detailed": "true"},
    )


def test_settings_of_a_key_pi_hole_does_not_know_is_refused(serve: Serve) -> None:
    # FTL answers an unknown key with an empty config, not an error.
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve({"config": {}, "took": 0.0001})) as api:
        with pytest.raises(ArgumentError, match="isn't a setting or a topic") as error:
            api.config.settings("dns.nope")

    assert error.value.parameter == "key"


@pytest.mark.parametrize("key", ["webserver", "webserver.api", "webserver.port", "misc", "misc.dnsmasq_lines", "files"])
def test_settings_and_update_refuse_keys_outside_the_allowlist(
    key: str, serve: Serve, sent: list[httpx2.Request]
) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve({})) as api:
        with pytest.raises(ArgumentError, match="outside the settings gravitywell covers"):
            api.config.settings(key)
        with pytest.raises(ArgumentError, match="outside the settings gravitywell covers"):
            api.config.update({key: True})

    assert sent == []


def test_update_patches_nested_settings_and_returns_their_new_values(serve: Serve, sent: list[httpx2.Request]) -> None:
    body = {"config": {"dns": {"dnssec": True}, "misc": {"privacylevel": 1, "nice": -10}}, "took": 0.02}
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(body)) as api:
        changed = api.config.update({"dns.dnssec": True, "misc.privacylevel": 1})

    assert (changed.settings, changed.took) == ({"dns.dnssec": True, "misc.privacylevel": 1}, 0.02)
    assert [(request.method, request.url.path) for request in sent] == [
        ("GET", "/api/config"),
        ("PATCH", "/api/config"),
    ]
    assert sent[1].content == b'{"config":{"dns":{"dnssec":true},"misc":{"privacylevel":1}}}'


def test_update_refuses_keys_that_are_not_settings(serve: Serve, sent: list[httpx2.Request]) -> None:
    # A `PATCH` would skip them silently.
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve({"config": {"dns": {"dnssec": True}}})) as api:
        with pytest.raises(ArgumentError, match="`dns.dnsec` isn't a setting"):
            api.config.update({"dns.dnsec": True})
        with pytest.raises(ArgumentError, match="`dns` isn't a setting"):
            api.config.update({"dns": {"dnssec": True}})

    assert [request.method for request in sent] == ["GET", "GET"]


@pytest.mark.parametrize(
    "key",
    ["dns.port", "dns.interface", "dns.hosts", "dns.cnameRecords", "dns.upstreams", "dns.revServers", "dhcp.hosts"],
)
def test_update_refuses_the_dns_port_and_interface_and_the_lists_with_their_own_methods(
    key: str, serve: Serve, sent: list[httpx2.Request]
) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve({})) as api:
        with pytest.raises(ArgumentError, match="can't be changed with `update`"):
            api.config.update({key: []})
        with pytest.raises(ArgumentError, match="at least one setting"):
            api.config.update({})

    assert sent == []


def test_reverse_servers_read_whether_enabled_network_server_and_domain(
    serve: Serve, sent: list[httpx2.Request]
) -> None:
    body = {
        "config": {"dns": {"revServers": ["true,192.168.1.0/24,192.168.1.1,lan", "false,10.0.0.0/8,10.0.0.1#5353"]}},
        "took": 0.1,
    }
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(body)) as api:
        servers = api.config.reverse_servers().servers

    assert [(s.enabled, s.network, s.server, s.domain) for s in servers] == [
        (True, "192.168.1.0/24", "192.168.1.1", "lan"),
        (False, "10.0.0.0/8", "10.0.0.1#5353", None),
    ]
    [request] = sent
    assert request.url.path == "/api/config/dns/revServers"


def test_static_leases_read_mac_ip_hostname_and_lease_time(serve: Serve) -> None:
    # dnsmasq's `dhcp-host` forms: tags, client IDs and IPv6 in brackets too.
    entries = [
        "00:20:e0:3b:13:af,192.168.0.123,laptop,24h",
        "00:20:e0:ab:cd:ef,id:*,set:office,[fd00::5],desktop,infinite",
        "12:34:56:78:9a:bc,192.168.0.9",
    ]
    with PiHole(
        BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve({"config": {"dhcp": {"hosts": entries}}, "took": 0.1})
    ) as api:
        leases = api.config.static_leases().leases

    assert [(lease.hwaddr, lease.ip, lease.hostname, lease.lease_time) for lease in leases] == [
        ("00:20:e0:3b:13:af", "192.168.0.123", "laptop", "24h"),
        ("00:20:e0:ab:cd:ef", "fd00::5", "desktop", "infinite"),
        ("12:34:56:78:9a:bc", "192.168.0.9", None, None),
    ]


def test_add_reverse_server_and_static_lease_put_one_entry_each(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve({})) as api:
        api.config.add_reverse_server("192.168.1.0/24", "192.168.1.1", "lan")
        api.config.add_reverse_server("10.0.0.0/8", "10.0.0.1#5353", enabled=False)
        api.config.add_static_lease("12:34:56:78:9a:bc", "192.168.1.50", "laptop")
        api.config.add_static_lease("12:34:56:78:9a:bd", "192.168.1.51")

    assert [request.url.path for request in sent] == [
        "/api/config/dns/revServers/true,192.168.1.0/24,192.168.1.1,lan",
        "/api/config/dns/revServers/false,10.0.0.0/8,10.0.0.1#5353",
        "/api/config/dhcp/hosts/12:34:56:78:9a:bc,192.168.1.50,laptop",
        "/api/config/dhcp/hosts/12:34:56:78:9a:bd,192.168.1.51",
    ]
    assert {request.method for request in sent} == {"PUT"}


def test_deletes_send_the_stored_reverse_server_and_static_lease(serve: Serve, sent: list[httpx2.Request]) -> None:
    body = {
        "config": {
            "dns": {"revServers": ["true,192.168.1.0/24,192.168.1.1,lan"]},
            "dhcp": {"hosts": ["12:34:56:78:9a:bc,192.168.1.50,laptop,24h"]},
        },
        "took": 0.1,
    }
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(body)) as api:
        api.config.delete_reverse_server("192.168.1.0/24", "192.168.1.1")
        api.config.delete_static_lease("12:34:56:78:9A:BC")

    assert [(request.method, request.url.path) for request in sent] == [
        ("GET", "/api/config/dns/revServers"),
        ("DELETE", "/api/config/dns/revServers/true,192.168.1.0/24,192.168.1.1,lan"),
        ("GET", "/api/config/dhcp/hosts"),
        ("DELETE", "/api/config/dhcp/hosts/12:34:56:78:9a:bc,192.168.1.50,laptop,24h"),
    ]


def test_deleting_a_missing_or_ambiguous_entry_is_refused(serve: Serve) -> None:
    body = {
        "config": {
            "dns": {"revServers": ["true,192.168.1.0/24,192.168.1.1,lan"]},
            "dhcp": {"hosts": ["12:34:56:78:9a:bc,192.168.1.50", "12:34:56:78:9a:bc,set:x,192.168.1.51"]},
        },
        "took": 0.1,
    }
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(body)) as api:
        with pytest.raises(ArgumentError, match="No reverse server forwards"):
            api.config.delete_reverse_server("192.168.1.0/24", "192.168.1.254")
        with pytest.raises(ArgumentError, match="No static lease names"):
            api.config.delete_static_lease("12:34:56:78:9a:bd")
        with pytest.raises(ArgumentError, match="Several static leases name"):
            api.config.delete_static_lease("12:34:56:78:9a:bc")


def test_names_that_would_split_a_reverse_server_or_static_lease_are_refused(
    serve: Serve, sent: list[httpx2.Request]
) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve({})) as api:
        with pytest.raises(ArgumentError) as server:
            api.config.add_reverse_server("192.168.1.0/24", "192.168.1.1,x")
        with pytest.raises(ArgumentError) as domain:
            api.config.add_reverse_server("192.168.1.0/24", "192.168.1.1", "my lan")
        with pytest.raises(ArgumentError) as hostname:
            api.config.add_static_lease("12:34:56:78:9a:bc", "192.168.1.50", "a,b")

    assert (server.value.parameter, domain.value.parameter, hostname.value.parameter) == (
        "server",
        "domain",
        "hostname",
    )
    assert sent == []


@pytest.mark.anyio
async def test_async_settings_methods_send_the_same_requests(serve: Serve, sent: list[httpx2.Request]) -> None:
    body = {
        "config": {
            "dns": {"dnssec": False, "revServers": ["true,192.168.1.0/24,192.168.1.1,lan"]},
            "dhcp": {"hosts": ["12:34:56:78:9a:bc,192.168.1.50"]},
            "debug": {"api": setting(False)},
        },
        "took": 0.1,
    }
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(body)) as api:
        assert [s.key for s in (await api.config.settings("debug")).settings] == ["debug.api"]
        assert (await api.config.update({"dns.dnssec": False})).settings == {"dns.dnssec": False}
        await api.config.add_reverse_server("192.168.1.0/24", "192.168.1.1", "lan")
        await api.config.delete_reverse_server("192.168.1.0/24", "192.168.1.1")
        await api.config.add_static_lease("12:34:56:78:9a:bc", "192.168.1.50", "laptop")
        await api.config.delete_static_lease("12:34:56:78:9a:bc")

    assert [request.method for request in sent] == [
        "GET",
        "GET",
        "PATCH",
        "PUT",
        "GET",
        "DELETE",
        "PUT",
        "GET",
        "DELETE",
    ]


def test_ai_tools_mark_only_the_deletes_and_changes_destructive() -> None:
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
        "config_settings": (True, False),
        "config_update": (False, True),
        "config_reverse_servers": (True, False),
        "config_add_reverse_server": (False, False),
        "config_delete_reverse_server": (False, True),
        "config_static_leases": (True, False),
        "config_add_static_lease": (False, False),
        "config_delete_static_lease": (False, True),
    }
