from collections.abc import Callable

import httpx2
import pytest
from clientx.tools import list_tools

from gravitywell import AsyncPiHole, PiHole, PiHoleAuth
from gravitywell.models import RestoreParts

BASE_URL = "http://pi.hole"
PASSWORD = "app-password"
# conftest.py's `serve` fixture.
type Serve = Callable[[object], httpx2.MockTransport]

ARCHIVE = b"PK\x03\x04" + b"\x00" * 64
RESTORED_BODY = {"files": ["etc/pihole/pihole.toml", "etc/pihole/gravity.db->group"], "took": 0.003}
EVERY_PART = (
    b'{"config":true,"dhcp_leases":true,"gravity":{"group":true,"adlist":true,"adlist_by_group":true,'
    b'"domainlist":true,"domainlist_by_group":true,"client":true,"client_by_group":true}}'
)


def test_export_streams_the_archive(serve: Serve, sent: list[httpx2.Request]) -> None:
    body = httpx2.Response(200, content=ARCHIVE, headers={"Content-Type": "application/zip"})
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(body)) as api:
        assert b"".join(api.teleporter.export()) == ARCHIVE

    [request] = sent
    assert (request.method, request.url.path) == ("GET", "/api/teleporter")


@pytest.mark.anyio
async def test_async_export_streams_the_archive(serve: Serve) -> None:
    body = httpx2.Response(200, content=ARCHIVE, headers={"Content-Type": "application/zip"})
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(body)) as api:
        assert b"".join([chunk async for chunk in await api.teleporter.export()]) == ARCHIVE


def test_restore_uploads_a_zip_and_asks_for_every_part(serve: Serve, sent: list[httpx2.Request]) -> None:
    with PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(RESTORED_BODY)) as api:
        assert api.teleporter.restore(ARCHIVE).files == RESTORED_BODY["files"]

    [request] = sent
    assert (request.method, request.url.path) == ("POST", "/api/teleporter")
    assert request.headers["Content-Type"].startswith("multipart/form-data")
    assert b'name="file"; filename="teleporter.zip"' in request.content
    assert b'name="import"' in request.content
    assert EVERY_PART in request.content


@pytest.mark.anyio
async def test_restore_names_a_gzip_archive_tar_gz_and_sends_the_parts_chosen(
    serve: Serve, sent: list[httpx2.Request]
) -> None:
    async with AsyncPiHole(BASE_URL, auth=PiHoleAuth(PASSWORD), transport=serve(RESTORED_BODY)) as api:
        await api.teleporter.restore(b"\x1f\x8b\x08\x00", RestoreParts(config=False, dhcp_leases=False))

    [request] = sent
    assert b'filename="teleporter.tar.gz"' in request.content
    assert b'{"config":false,"dhcp_leases":false,' in request.content


def test_teleporter_is_not_an_ai_tool() -> None:
    # A backup holds the password hashes, and a restore overwrites everything.
    names = [tool.name for tool in list_tools(PiHole(BASE_URL, auth=PiHoleAuth(PASSWORD)))]

    assert [name for name in names if name.startswith("teleporter")] == []
