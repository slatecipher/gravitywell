"""The information endpoints, under `/info`."""

from clientx import AsyncResource, Resource, method

from gravitywell.models import (
    DatabaseInfoResponse,
    FtlInfoResponse,
    HostInfoResponse,
    MetricsResponse,
    SensorsResponse,
    SystemInfoResponse,
    VersionResponse,
)


class Info(Resource, prefix="/info"):
    """Information about the Pi-hole: its versions, machine and DNS server."""

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
