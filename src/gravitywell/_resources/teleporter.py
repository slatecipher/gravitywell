"""The Teleporter endpoints, under `/teleporter`: backups, for Python only.

A backup holds the password hashes, and a restore overwrites everything, so
neither is an AI tool: `export` says so with ClientX's `include_in_tools=False`,
and `restore` is a plain method over a private endpoint.
"""

from collections.abc import AsyncIterator, Iterator
from typing import Annotated

from clientx import AsyncResource, File, Form, Resource, Send, method

from gravitywell.models import RestoreParts, RestoreResponse

_GZIP_MAGIC = b"\x1f\x8b"


def _archive_file(archive: bytes) -> tuple[str, bytes, str]:
    """Name the upload by its type, as FTL accepts only `.zip` and `.tar.gz`."""
    if archive.startswith(_GZIP_MAGIC):
        return ("teleporter.tar.gz", archive, "application/gzip")
    return ("teleporter.zip", archive, "application/zip")


class Teleporter(Resource, prefix="/teleporter", tags=["teleporter"]):
    """Teleporter backups of the Pi-hole, for Python only."""

    # It holds the password hashes: never an AI tool, whatever its type.
    @method.get("", include_in_tools=False)
    def export(self) -> Iterator[bytes]:
        """Download a Teleporter backup of the Pi-hole, as a zip archive.

        It holds the settings (`pihole.toml`, with local DNS records, password
        hashes and the TOTP secret), the gravity database's groups, lists,
        domain rules and clients, the DHCP leases, the hosts file, and the
        network devices and diagnosis messages. Keep it as safe as a password.
        It's a stream: write each chunk to a file as it comes, with
        `async for chunk in await ...` in the async client. Not an AI tool, as
        it holds the password hashes.
        With an application password, it answers with an error (403) unless
        the Pi-hole's `webserver.api.app_sudo` setting is on.

        Yields:
            The archive, in chunks.
        """
        ...

    # The raw request for `restore` below, which names the file as FTL needs.
    @method.post("")
    def _restore(
        self,
        file: Annotated[tuple[str, bytes, str], File()],
        parts: Annotated[RestoreParts, Form(alias="import"), Send(json_part=True)],
    ) -> RestoreResponse: ...

    def restore(self, archive: bytes, parts: RestoreParts | None = None) -> RestoreResponse:
        """Restore the Pi-hole from a Teleporter backup, replacing its contents.

        Each part restored overwrites the current one: the settings, the DHCP
        leases, and each gravity table, such as the domain rules. FTL restarts
        afterwards, so DNS and the API pause for a few seconds. It takes the
        zip archives `export` makes, and Pi-hole v5's `.tar.gz` ones. Not an
        AI tool.
        With an application password, it answers with an error (403) unless
        the Pi-hole's `webserver.api.app_sudo` setting is on.

        Args:
            archive: The archive's bytes, such as a file `export` wrote.
            parts: What to restore. Everything by default.

        Returns:
            The files and gravity tables restored.
        """
        return self._restore(_archive_file(archive), parts or RestoreParts())


class AsyncTeleporter(AsyncResource, prefix="/teleporter", tags=["teleporter"]):
    """Teleporter backups of the Pi-hole, for Python only."""

    # It holds the password hashes: never an AI tool, whatever its type.
    @method.get("", include_in_tools=False)
    async def export(self) -> AsyncIterator[bytes]:
        """Download a Teleporter backup of the Pi-hole, as a zip archive.

        It holds the settings (`pihole.toml`, with local DNS records, password
        hashes and the TOTP secret), the gravity database's groups, lists,
        domain rules and clients, the DHCP leases, the hosts file, and the
        network devices and diagnosis messages. Keep it as safe as a password.
        It's a stream: write each chunk to a file as it comes, with
        `async for chunk in await ...` in the async client. Not an AI tool, as
        it holds the password hashes.
        With an application password, it answers with an error (403) unless
        the Pi-hole's `webserver.api.app_sudo` setting is on.

        Yields:
            The archive, in chunks.
        """
        ...

    # The raw request for `restore` below, which names the file as FTL needs.
    @method.post("")
    async def _restore(
        self,
        file: Annotated[tuple[str, bytes, str], File()],
        parts: Annotated[RestoreParts, Form(alias="import"), Send(json_part=True)],
    ) -> RestoreResponse: ...

    async def restore(self, archive: bytes, parts: RestoreParts | None = None) -> RestoreResponse:
        """Restore the Pi-hole from a Teleporter backup, replacing its contents.

        Each part restored overwrites the current one: the settings, the DHCP
        leases, and each gravity table, such as the domain rules. FTL restarts
        afterwards, so DNS and the API pause for a few seconds. It takes the
        zip archives `export` makes, and Pi-hole v5's `.tar.gz` ones. Not an
        AI tool.
        With an application password, it answers with an error (403) unless
        the Pi-hole's `webserver.api.app_sudo` setting is on.

        Args:
            archive: The archive's bytes, such as a file `export` wrote.
            parts: What to restore. Everything by default.

        Returns:
            The files and gravity tables restored.
        """
        return await self._restore(_archive_file(archive), parts or RestoreParts())
