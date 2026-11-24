"""The information endpoints, under `/info`."""

from typing import Annotated

from clientx import AsyncResource, Resource, method
from clientx.tools import tool
from pydantic import Field

from gravitywell.models import (
    DatabaseInfoResponse,
    FtlInfoResponse,
    HostInfoResponse,
    MessageCountResponse,
    MessagesResponse,
    MetricsResponse,
    SensorsResponse,
    SystemInfoResponse,
    VersionResponse,
)


class Info(Resource, prefix="/info"):
    """Information about the Pi-hole: its versions, machine and DNS server."""

    @method.get("/messages")
    def messages(self) -> MessagesResponse:
        """Fetch the problems the Pi-hole reports on its diagnosis page.

        Use it first when something seems wrong: messages report invalid
        regex rules, lists that failed to download, unreachable upstream
        servers, rate-limited clients, a disk or memory running out, and
        more. Fixing the cause doesn't remove a message: delete it once it's
        dealt with. It changes nothing.
        """
        ...

    @method.get("/messages/count")
    def message_count(self) -> MessageCountResponse:
        """Fetch how many problems the Pi-hole reports.

        A quick check before fetching the messages themselves. It changes
        nothing.
        """
        ...

    # The raw request for `delete_messages` below, which joins the IDs into
    # one path segment. ClientX leaves private names out of AI tools.
    @method.delete("/messages/{ids}")
    def _delete_messages(self, ids: str) -> None: ...

    @tool(destructive=True, idempotent=True)
    def delete_messages(self, ids: Annotated[list[int], Field(min_length=1)]) -> None:
        """Delete diagnosis messages, such as ones whose problem is fixed.

        It only removes the messages: a problem that persists is reported
        again. If none of the messages exists, it answers with an error (404);
        otherwise missing ones are skipped.

        Args:
            ids: The messages' IDs, as `messages` shows them, such as `[3, 4]`.
        """
        self._delete_messages(",".join(str(message_id) for message_id in ids))

    @method.get("/system")
    def system(self) -> SystemInfoResponse:
        """Fetch the Pi-hole machine's uptime, memory, processes and CPU use.

        Use it to check whether the machine is overloaded, such as when DNS
        answers are slow, and how much of it FTL, Pi-hole's DNS server, uses.
        It changes nothing.
        """
        ...

    @method.get("/host")
    def host(self) -> HostInfoResponse:
        """Fetch the Pi-hole machine's operating system and hardware model.

        Use it to tell what the Pi-hole runs on, such as a Raspberry Pi model
        or a container on another machine. It changes nothing.
        """
        ...

    @method.get("/sensors")
    def sensors(self) -> SensorsResponse:
        """Fetch the Pi-hole machine's hardware sensors and CPU temperature.

        Use it to check whether the machine runs hot: compare `cpu_temp` with
        `hot_limit`. A container or virtual machine may report no sensors. It
        changes nothing.
        """
        ...

    @method.get("/ftl")
    def ftl(self) -> FtlInfoResponse:
        """Fetch FTL's database contents, privacy level and resource use.

        FTL is Pi-hole's DNS server. It reports how many blocked domains,
        lists, groups, clients and rules the gravity database holds, the
        privacy level, which decides what statistics hide, whether the API
        allows destructive actions, and FTL's own memory and CPU use. It
        changes nothing.
        """
        ...

    @method.get("/database")
    def database(self) -> DatabaseInfoResponse:
        """Fetch the query database's size and how many queries it holds.

        Use it to find how far back queries go, in memory and in the database
        file, before asking for an older time range. It changes nothing.
        """
        ...

    @method.get("/metrics")
    def metrics(self) -> MetricsResponse:
        """Fetch FTL's DNS cache and reply counters, and its DHCP counters.

        The counts run from FTL's start. Use them to judge the DNS cache, such
        as `evicted` growing when it's too small, and how queries were
        answered: locally, forwarded, stale or not at all. The DHCP counters
        are zero unless the Pi-hole serves DHCP. It changes nothing.
        """
        ...

    @method.get("/version")
    def version(self) -> VersionResponse:
        """Fetch the installed versions of the Pi-hole's components.

        Pi-hole has three: core (its scripts and the `pihole` command), web
        (the web interface) and FTL (the DNS server, which also serves this
        API). Use it to check which Pi-hole release runs, such as before
        reporting a problem.
        """
        ...


class AsyncInfo(AsyncResource, prefix="/info"):
    """Information about the Pi-hole: its versions, machine and DNS server."""

    @method.get("/messages")
    async def messages(self) -> MessagesResponse:
        """Fetch the problems the Pi-hole reports on its diagnosis page.

        Use it first when something seems wrong: messages report invalid
        regex rules, lists that failed to download, unreachable upstream
        servers, rate-limited clients, a disk or memory running out, and
        more. Fixing the cause doesn't remove a message: delete it once it's
        dealt with. It changes nothing.
        """
        ...

    @method.get("/messages/count")
    async def message_count(self) -> MessageCountResponse:
        """Fetch how many problems the Pi-hole reports.

        A quick check before fetching the messages themselves. It changes
        nothing.
        """
        ...

    # The raw request for `delete_messages` below, which joins the IDs into
    # one path segment. ClientX leaves private names out of AI tools.
    @method.delete("/messages/{ids}")
    async def _delete_messages(self, ids: str) -> None: ...

    @tool(destructive=True, idempotent=True)
    async def delete_messages(self, ids: Annotated[list[int], Field(min_length=1)]) -> None:
        """Delete diagnosis messages, such as ones whose problem is fixed.

        It only removes the messages: a problem that persists is reported
        again. If none of the messages exists, it answers with an error (404);
        otherwise missing ones are skipped.

        Args:
            ids: The messages' IDs, as `messages` shows them, such as `[3, 4]`.
        """
        await self._delete_messages(",".join(str(message_id) for message_id in ids))

    @method.get("/system")
    async def system(self) -> SystemInfoResponse:
        """Fetch the Pi-hole machine's uptime, memory, processes and CPU use.

        Use it to check whether the machine is overloaded, such as when DNS
        answers are slow, and how much of it FTL, Pi-hole's DNS server, uses.
        It changes nothing.
        """
        ...

    @method.get("/host")
    async def host(self) -> HostInfoResponse:
        """Fetch the Pi-hole machine's operating system and hardware model.

        Use it to tell what the Pi-hole runs on, such as a Raspberry Pi model
        or a container on another machine. It changes nothing.
        """
        ...

    @method.get("/sensors")
    async def sensors(self) -> SensorsResponse:
        """Fetch the Pi-hole machine's hardware sensors and CPU temperature.

        Use it to check whether the machine runs hot: compare `cpu_temp` with
        `hot_limit`. A container or virtual machine may report no sensors. It
        changes nothing.
        """
        ...

    @method.get("/ftl")
    async def ftl(self) -> FtlInfoResponse:
        """Fetch FTL's database contents, privacy level and resource use.

        FTL is Pi-hole's DNS server. It reports how many blocked domains,
        lists, groups, clients and rules the gravity database holds, the
        privacy level, which decides what statistics hide, whether the API
        allows destructive actions, and FTL's own memory and CPU use. It
        changes nothing.
        """
        ...

    @method.get("/database")
    async def database(self) -> DatabaseInfoResponse:
        """Fetch the query database's size and how many queries it holds.

        Use it to find how far back queries go, in memory and in the database
        file, before asking for an older time range. It changes nothing.
        """
        ...

    @method.get("/metrics")
    async def metrics(self) -> MetricsResponse:
        """Fetch FTL's DNS cache and reply counters, and its DHCP counters.

        The counts run from FTL's start. Use them to judge the DNS cache, such
        as `evicted` growing when it's too small, and how queries were
        answered: locally, forwarded, stale or not at all. The DHCP counters
        are zero unless the Pi-hole serves DHCP. It changes nothing.
        """
        ...

    @method.get("/version")
    async def version(self) -> VersionResponse:
        """Fetch the installed versions of the Pi-hole's components.

        Pi-hole has three: core (its scripts and the `pihole` command), web
        (the web interface) and FTL (the DNS server, which also serves this
        API). Use it to check which Pi-hole release runs, such as before
        reporting a problem.
        """
        ...
