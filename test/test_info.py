import httpx2
import pytest

from gravitywell import AsyncPiHole, PiHole, PiHoleAuth
from gravitywell.models import VersionResponse

BASE_URL = "http://pi.hole"
PASSWORD = "app-password"
# What the auth's login and logout get, around the endpoint's request.
SESSION_BODY = {"session": {"sid": "sid-1"}, "took": 0.003}

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


def test_version_gets_info_version_and_reads_the_installed_versions() -> None:
    sent: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        if request.url.path == "/api/auth":
            return httpx2.Response(200, json=SESSION_BODY)
        sent.append(request)
        return httpx2.Response(200, json=VERSION_BODY)

    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=httpx2.MockTransport(handler)) as api:
        assert installed(api.info.version()) == ("v6.1", "v6.2", "v6.3")

    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/info/version")


@pytest.mark.anyio
async def test_async_version_gets_info_version_and_reads_the_installed_versions() -> None:
    sent: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        if request.url.path == "/api/auth":
            return httpx2.Response(200, json=SESSION_BODY)
        sent.append(request)
        return httpx2.Response(200, json=VERSION_BODY)

    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=httpx2.MockTransport(handler)) as api:
        assert installed(await api.info.version()) == ("v6.1", "v6.2", "v6.3")

    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/info/version")
