"""The statistics endpoints, under `/stats`."""

from typing import Annotated

from clientx import AsyncResource, Query, Resource, method

from gravitywell.models import (
    DatabaseSummaryResponse,
    DatabaseTopClientsResponse,
    DatabaseTopDomainsResponse,
    DatabaseUpstreamsResponse,
    QueryTypesResponse,
    RecentBlockedResponse,
    SummaryResponse,
    TimeRange,
    TopClientsResponse,
    TopDomainsResponse,
    UpstreamsResponse,
)


class StatsDatabase(Resource, prefix="/stats/database", tags=["stats"]):
    """Statistics over a time range, from the Pi-hole's query database."""

    @method.get("/summary")
    def summary(self, time_range: Annotated[TimeRange, Query()]) -> DatabaseSummaryResponse:
        """Fetch totals of the Pi-hole's queries over a time range.

        It reads the query database, which keeps queries for 91 days by
        default and gets each one within about a minute, so it can answer
        questions such as how many queries were blocked last week. For the
        last 24 hours, the stats summary has more detail. It changes nothing.

        Args:
            time_range: The range to cover: `start`, and `until`, now by
                default, both with a timezone.
        """
        ...

    @method.get("/top_domains")
    def top_domains(
        self,
        time_range: Annotated[TimeRange, Query()],
        blocked: Annotated[bool, Query()] = False,
        count: Annotated[int, Query(ge=1)] = 10,
    ) -> DatabaseTopDomainsResponse:
        """Fetch the most queried domains over a time range.

        It reads the query database, which keeps queries for 91 days by
        default. By default it ranks domains by permitted queries, so blocked
        domains don't appear; pass `blocked=true` to rank them by blocked
        queries. It changes nothing.

        Args:
            time_range: The range to cover: `start`, and `until`, now by
                default, both with a timezone.
            blocked: `true` to rank domains by blocked queries, `false` (the
                default) by permitted queries.
            count: How many domains to return, at least 1. 10 by default.
        """
        ...

    @method.get("/top_clients")
    def top_clients(
        self,
        time_range: Annotated[TimeRange, Query()],
        blocked: Annotated[bool, Query()] = False,
        count: Annotated[int, Query(ge=1)] = 10,
    ) -> DatabaseTopClientsResponse:
        """Fetch the clients that sent the most queries over a time range.

        It reads the query database, which keeps queries for 91 days by
        default. By default it ranks clients by permitted queries (the
        last-24-hours list counts all of a client's queries instead); pass
        `blocked=true` to rank them by blocked queries. It changes nothing.

        Args:
            time_range: The range to cover: `start`, and `until`, now by
                default, both with a timezone.
            blocked: `true` to rank clients by blocked queries, `false` (the
                default) by permitted queries.
            count: How many clients to return, at least 1. 10 by default.
        """
        ...

    @method.get("/upstreams")
    def upstreams(self, time_range: Annotated[TimeRange, Query()]) -> DatabaseUpstreamsResponse:
        """Fetch where the Pi-hole's queries went over a time range.

        It reads the query database, which keeps queries for 91 days by
        default: how many queries each upstream DNS server answered, how many
        came from the cache, and how many were blocked. The database keeps
        no response times; the last-24-hours upstreams list has them. It
        changes nothing.

        Args:
            time_range: The range to cover: `start`, and `until`, now by
                default, both with a timezone.
        """
        ...

    @method.get("/query_types")
    def query_types(self, time_range: Annotated[TimeRange, Query()]) -> QueryTypesResponse:
        """Fetch the Pi-hole's queries by DNS record type over a time range.

        It reads the query database, which keeps queries for 91 days by
        default. `A` and `AAAA` are IPv4 and IPv6 address lookups, `PTR`
        reverse lookups, `HTTPS` HTTPS service records, and so on. It changes
        nothing.

        Args:
            time_range: The range to cover: `start`, and `until`, now by
                default, both with a timezone.
        """
        ...


class Stats(Resource, prefix="/stats", tags=["stats"]):
    """Statistics about the Pi-hole's activity."""

    database = StatsDatabase()

    @method.get("/summary")
    def summary(self) -> SummaryResponse:
        """Fetch totals of the Pi-hole's queries, clients and blocklists.

        The counts cover the history the Pi-hole keeps, the last 24 hours by
        default. Use it for totals and shares, such as how many queries were
        blocked and what percentage that is, how many were answered from the
        cache, how many devices use the Pi-hole, or how many domains its
        blocklists hold and when they were last updated. It changes nothing.
        """
        ...

    @method.get("/top_domains")
    def top_domains(
        self,
        blocked: Annotated[bool, Query()] = False,
        count: Annotated[int, Query(ge=1)] = 10,
    ) -> TopDomainsResponse:
        """Fetch the most queried domains, permitted or blocked.

        The counts cover the history the Pi-hole keeps, the last 24 hours by
        default. By default it ranks domains by permitted queries, so blocked
        domains don't appear; pass `blocked=true` to rank them by blocked
        queries, such as to see which ad or tracking domains devices ask for
        most. Domains excluded in the Pi-hole's settings are left out, and the
        list is empty if its privacy level hides domains. It changes nothing.

        Args:
            blocked: `true` to rank domains by blocked queries, `false` (the
                default) by permitted queries.
            count: How many domains to return, at least 1. 10 by default.
        """
        ...

    @method.get("/top_clients")
    def top_clients(
        self,
        blocked: Annotated[bool, Query()] = False,
        count: Annotated[int, Query(ge=1)] = 10,
    ) -> TopClientsResponse:
        """Fetch the clients that sent the Pi-hole the most queries.

        A client is a device on the network, known by its IP address and, if
        the Pi-hole knows one, its hostname. The counts cover the history the
        Pi-hole keeps, the last 24 hours by default. By default it ranks
        clients by all their queries, blocked or not; pass `blocked=true` to
        rank them by blocked queries only. Clients excluded in the Pi-hole's
        settings are left out, and the list is empty if its privacy level
        hides clients. It changes nothing.

        Args:
            blocked: `true` to rank clients by blocked queries only, `false`
                (the default) by all their queries.
            count: How many clients to return, at least 1. 10 by default.
        """
        ...

    @method.get("/upstreams")
    def upstreams(self) -> UpstreamsResponse:
        """Fetch the Pi-hole's upstream DNS servers, with counts and speeds.

        Upstream servers answer the queries the Pi-hole doesn't block or
        answer from its cache. The list starts with `blocklist` (queries
        blocked) and `cache` (queries answered from the cache), then each
        server that answered a query in the history the Pi-hole keeps, the
        last 24 hours by default, with its average response time. Use it to
        see which servers the Pi-hole forwards to, and whether one is slow.
        It changes nothing.
        """
        ...

    @method.get("/query_types")
    def query_types(self) -> QueryTypesResponse:
        """Fetch how many queries of each DNS record type the Pi-hole got.

        The counts cover the history the Pi-hole keeps, the last 24 hours by
        default: `A` and `AAAA` for IPv4 and IPv6 addresses, `PTR` for
        reverse lookups, `HTTPS` for HTTPS service records, and so on. The
        stats summary holds the same counts alongside its totals; use this
        for the record types alone. It changes nothing.
        """
        ...

    @method.get("/recent_blocked")
    def recent_blocked(self, count: Annotated[int, Query(ge=1)] = 1) -> RecentBlockedResponse:
        """Fetch the domains the Pi-hole blocked most recently.

        Newest first, one entry per blocked query, so a domain blocked again
        appears again. Use it to see what was just blocked, such as when a
        website or app stops working. `hidden` stands for a domain the
        privacy level hid, and the list is empty if the privacy level hides
        domains. It changes nothing.

        Args:
            count: How many blocked queries to return, at least 1. 1 by
                default.
        """
        ...


class AsyncStatsDatabase(AsyncResource, prefix="/stats/database", tags=["stats"]):
    """Statistics over a time range, from the Pi-hole's query database."""

    @method.get("/summary")
    async def summary(self, time_range: Annotated[TimeRange, Query()]) -> DatabaseSummaryResponse:
        """Fetch totals of the Pi-hole's queries over a time range.

        It reads the query database, which keeps queries for 91 days by
        default and gets each one within about a minute, so it can answer
        questions such as how many queries were blocked last week. For the
        last 24 hours, the stats summary has more detail. It changes nothing.

        Args:
            time_range: The range to cover: `start`, and `until`, now by
                default, both with a timezone.
        """
        ...

    @method.get("/top_domains")
    async def top_domains(
        self,
        time_range: Annotated[TimeRange, Query()],
        blocked: Annotated[bool, Query()] = False,
        count: Annotated[int, Query(ge=1)] = 10,
    ) -> DatabaseTopDomainsResponse:
        """Fetch the most queried domains over a time range.

        It reads the query database, which keeps queries for 91 days by
        default. By default it ranks domains by permitted queries, so blocked
        domains don't appear; pass `blocked=true` to rank them by blocked
        queries. It changes nothing.

        Args:
            time_range: The range to cover: `start`, and `until`, now by
                default, both with a timezone.
            blocked: `true` to rank domains by blocked queries, `false` (the
                default) by permitted queries.
            count: How many domains to return, at least 1. 10 by default.
        """
        ...

    @method.get("/top_clients")
    async def top_clients(
        self,
        time_range: Annotated[TimeRange, Query()],
        blocked: Annotated[bool, Query()] = False,
        count: Annotated[int, Query(ge=1)] = 10,
    ) -> DatabaseTopClientsResponse:
        """Fetch the clients that sent the most queries over a time range.

        It reads the query database, which keeps queries for 91 days by
        default. By default it ranks clients by permitted queries (the
        last-24-hours list counts all of a client's queries instead); pass
        `blocked=true` to rank them by blocked queries. It changes nothing.

        Args:
            time_range: The range to cover: `start`, and `until`, now by
                default, both with a timezone.
            blocked: `true` to rank clients by blocked queries, `false` (the
                default) by permitted queries.
            count: How many clients to return, at least 1. 10 by default.
        """
        ...

    @method.get("/upstreams")
    async def upstreams(self, time_range: Annotated[TimeRange, Query()]) -> DatabaseUpstreamsResponse:
        """Fetch where the Pi-hole's queries went over a time range.

        It reads the query database, which keeps queries for 91 days by
        default: how many queries each upstream DNS server answered, how many
        came from the cache, and how many were blocked. The database keeps
        no response times; the last-24-hours upstreams list has them. It
        changes nothing.

        Args:
            time_range: The range to cover: `start`, and `until`, now by
                default, both with a timezone.
        """
        ...

    @method.get("/query_types")
    async def query_types(self, time_range: Annotated[TimeRange, Query()]) -> QueryTypesResponse:
        """Fetch the Pi-hole's queries by DNS record type over a time range.

        It reads the query database, which keeps queries for 91 days by
        default. `A` and `AAAA` are IPv4 and IPv6 address lookups, `PTR`
        reverse lookups, `HTTPS` HTTPS service records, and so on. It changes
        nothing.

        Args:
            time_range: The range to cover: `start`, and `until`, now by
                default, both with a timezone.
        """
        ...


class AsyncStats(AsyncResource, prefix="/stats", tags=["stats"]):
    """Statistics about the Pi-hole's activity."""

    database = AsyncStatsDatabase()

    @method.get("/summary")
    async def summary(self) -> SummaryResponse:
        """Fetch totals of the Pi-hole's queries, clients and blocklists.

        The counts cover the history the Pi-hole keeps, the last 24 hours by
        default. Use it for totals and shares, such as how many queries were
        blocked and what percentage that is, how many were answered from the
        cache, how many devices use the Pi-hole, or how many domains its
        blocklists hold and when they were last updated. It changes nothing.
        """
        ...

    @method.get("/top_domains")
    async def top_domains(
        self,
        blocked: Annotated[bool, Query()] = False,
        count: Annotated[int, Query(ge=1)] = 10,
    ) -> TopDomainsResponse:
        """Fetch the most queried domains, permitted or blocked.

        The counts cover the history the Pi-hole keeps, the last 24 hours by
        default. By default it ranks domains by permitted queries, so blocked
        domains don't appear; pass `blocked=true` to rank them by blocked
        queries, such as to see which ad or tracking domains devices ask for
        most. Domains excluded in the Pi-hole's settings are left out, and the
        list is empty if its privacy level hides domains. It changes nothing.

        Args:
            blocked: `true` to rank domains by blocked queries, `false` (the
                default) by permitted queries.
            count: How many domains to return, at least 1. 10 by default.
        """
        ...

    @method.get("/top_clients")
    async def top_clients(
        self,
        blocked: Annotated[bool, Query()] = False,
        count: Annotated[int, Query(ge=1)] = 10,
    ) -> TopClientsResponse:
        """Fetch the clients that sent the Pi-hole the most queries.

        A client is a device on the network, known by its IP address and, if
        the Pi-hole knows one, its hostname. The counts cover the history the
        Pi-hole keeps, the last 24 hours by default. By default it ranks
        clients by all their queries, blocked or not; pass `blocked=true` to
        rank them by blocked queries only. Clients excluded in the Pi-hole's
        settings are left out, and the list is empty if its privacy level
        hides clients. It changes nothing.

        Args:
            blocked: `true` to rank clients by blocked queries only, `false`
                (the default) by all their queries.
            count: How many clients to return, at least 1. 10 by default.
        """
        ...

    @method.get("/upstreams")
    async def upstreams(self) -> UpstreamsResponse:
        """Fetch the Pi-hole's upstream DNS servers, with counts and speeds.

        Upstream servers answer the queries the Pi-hole doesn't block or
        answer from its cache. The list starts with `blocklist` (queries
        blocked) and `cache` (queries answered from the cache), then each
        server that answered a query in the history the Pi-hole keeps, the
        last 24 hours by default, with its average response time. Use it to
        see which servers the Pi-hole forwards to, and whether one is slow.
        It changes nothing.
        """
        ...

    @method.get("/query_types")
    async def query_types(self) -> QueryTypesResponse:
        """Fetch how many queries of each DNS record type the Pi-hole got.

        The counts cover the history the Pi-hole keeps, the last 24 hours by
        default: `A` and `AAAA` for IPv4 and IPv6 addresses, `PTR` for
        reverse lookups, `HTTPS` for HTTPS service records, and so on. The
        stats summary holds the same counts alongside its totals; use this
        for the record types alone. It changes nothing.
        """
        ...

    @method.get("/recent_blocked")
    async def recent_blocked(self, count: Annotated[int, Query(ge=1)] = 1) -> RecentBlockedResponse:
        """Fetch the domains the Pi-hole blocked most recently.

        Newest first, one entry per blocked query, so a domain blocked again
        appears again. Use it to see what was just blocked, such as when a
        website or app stops working. `hidden` stands for a domain the
        privacy level hid, and the list is empty if the privacy level hides
        domains. It changes nothing.

        Args:
            count: How many blocked queries to return, at least 1. 1 by
                default.
        """
        ...
