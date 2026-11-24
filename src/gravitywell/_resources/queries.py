"""The query log endpoints, under `/queries`."""

from typing import Annotated

from clientx import AsyncResource, Query, Resource, method

from gravitywell.models import (
    DnssecStatus,
    QueryLogResponse,
    QueryStatus,
    QuerySuggestionsResponse,
    ReplyType,
    TimeRange,
)


class Queries(Resource, prefix="/queries", tags=["queries"]):
    """The Pi-hole's query log, one entry per DNS query."""

    @method.get()
    def log(
        self,
        time_range: Annotated[TimeRange | None, Query()] = None,
        domain: Annotated[str | None, Query()] = None,
        client_ip: Annotated[str | None, Query()] = None,
        client_name: Annotated[str | None, Query()] = None,
        upstream: Annotated[str | None, Query()] = None,
        query_type: Annotated[str | None, Query(alias="type")] = None,
        status: Annotated[QueryStatus | None, Query()] = None,
        reply: Annotated[ReplyType | None, Query()] = None,
        dnssec: Annotated[DnssecStatus | None, Query()] = None,
        disk: Annotated[bool, Query()] = False,
        count: Annotated[int, Query(alias="length", ge=1, le=10_000)] = 100,
        start: Annotated[int, Query(ge=0)] = 0,
        cursor: Annotated[int | None, Query(ge=0)] = None,
    ) -> QueryLogResponse:
        """Fetch DNS queries from the Pi-hole's query log, newest first.

        Each query shows the domain, the client that asked, what the Pi-hole
        did (`status`, such as `GRAVITY` for blocked by a blocklist), and the
        rule or list that decided it. Filters combine. `domain`, `client_ip`,
        `client_name` and `upstream` match exactly, or with `*` as a wildcard,
        such as `*doubleclick*`. It reads the queries in memory, the last 24
        hours by default, or with `disk` the query database, which keeps 91
        days by default. For more than `count` matches, page with `cursor`
        and `start`. The suggestions endpoint lists values to filter by. It
        changes nothing.

        Args:
            time_range: Only queries from `start` (included) to `until`
                (excluded), both with a timezone. `until` is now by default.
            domain: Only queries for this domain, such as `example.com`, or a
                pattern with `*`, such as `*.doubleclick.net`.
            client_ip: Only queries from this IP address, such as
                `192.168.1.235`, or a pattern with `*`, such as `192.168.1.*`.
            client_name: Only queries from this hostname, such as
                `laptop.lan`, or a pattern with `*`.
            upstream: Only queries answered by this upstream server, as
                `address#port`, such as `8.8.4.4#53`, or a pattern with `*`;
                or `blocklist` for blocked queries, `cache` for those answered
                from the cache, or `permitted` for those not blocked.
            query_type: Only queries for this record type, such as `A`,
                `AAAA` or `HTTPS`; `OTHER` for every type without a name of
                its own, or `TYPEnnn` for one of them.
            status: Only queries the Pi-hole handled this way, such as
                `GRAVITY` (blocked by a blocklist) or `FORWARDED`. For every
                blocked query, use `upstream=blocklist` instead.
            reply: Only queries with this kind of reply, such as `NXDOMAIN`.
            dnssec: Only queries with this DNSSEC status.
            disk: `true` to read the query database, which keeps queries for
                91 days by default, rather than the last 24 hours in memory.
            count: How many queries to return, from 1 to 10,000. 100 by
                default.
            start: How many matching queries to skip, for paging: `0` for the
                first page, then `count`, `2 * count` and so on, each with
                the first page's `cursor`.
            cursor: The `cursor` from the first page's response, so newer
                queries don't shift later pages. Leave it out for the first
                page.
        """
        ...

    @method.get("/suggestions")
    def suggestions(self, count: Annotated[int, Query(ge=1)] = 30) -> QuerySuggestionsResponse:
        """Fetch values to filter the query log by.

        It lists the domains, clients and upstream servers seen most, and
        every record type, status, reply and DNSSEC status the query log uses.
        Use it to find the exact names before filtering the log. It changes
        nothing.

        Args:
            count: How many domains and clients to suggest, at least 1. 30 by
                default.
        """
        ...


class AsyncQueries(AsyncResource, prefix="/queries", tags=["queries"]):
    """The Pi-hole's query log, one entry per DNS query."""

    @method.get()
    async def log(
        self,
        time_range: Annotated[TimeRange | None, Query()] = None,
        domain: Annotated[str | None, Query()] = None,
        client_ip: Annotated[str | None, Query()] = None,
        client_name: Annotated[str | None, Query()] = None,
        upstream: Annotated[str | None, Query()] = None,
        query_type: Annotated[str | None, Query(alias="type")] = None,
        status: Annotated[QueryStatus | None, Query()] = None,
        reply: Annotated[ReplyType | None, Query()] = None,
        dnssec: Annotated[DnssecStatus | None, Query()] = None,
        disk: Annotated[bool, Query()] = False,
        count: Annotated[int, Query(alias="length", ge=1, le=10_000)] = 100,
        start: Annotated[int, Query(ge=0)] = 0,
        cursor: Annotated[int | None, Query(ge=0)] = None,
    ) -> QueryLogResponse:
        """Fetch DNS queries from the Pi-hole's query log, newest first.

        Each query shows the domain, the client that asked, what the Pi-hole
        did (`status`, such as `GRAVITY` for blocked by a blocklist), and the
        rule or list that decided it. Filters combine. `domain`, `client_ip`,
        `client_name` and `upstream` match exactly, or with `*` as a wildcard,
        such as `*doubleclick*`. It reads the queries in memory, the last 24
        hours by default, or with `disk` the query database, which keeps 91
        days by default. For more than `count` matches, page with `cursor`
        and `start`. The suggestions endpoint lists values to filter by. It
        changes nothing.

        Args:
            time_range: Only queries from `start` (included) to `until`
                (excluded), both with a timezone. `until` is now by default.
            domain: Only queries for this domain, such as `example.com`, or a
                pattern with `*`, such as `*.doubleclick.net`.
            client_ip: Only queries from this IP address, such as
                `192.168.1.235`, or a pattern with `*`, such as `192.168.1.*`.
            client_name: Only queries from this hostname, such as
                `laptop.lan`, or a pattern with `*`.
            upstream: Only queries answered by this upstream server, as
                `address#port`, such as `8.8.4.4#53`, or a pattern with `*`;
                or `blocklist` for blocked queries, `cache` for those answered
                from the cache, or `permitted` for those not blocked.
            query_type: Only queries for this record type, such as `A`,
                `AAAA` or `HTTPS`; `OTHER` for every type without a name of
                its own, or `TYPEnnn` for one of them.
            status: Only queries the Pi-hole handled this way, such as
                `GRAVITY` (blocked by a blocklist) or `FORWARDED`. For every
                blocked query, use `upstream=blocklist` instead.
            reply: Only queries with this kind of reply, such as `NXDOMAIN`.
            dnssec: Only queries with this DNSSEC status.
            disk: `true` to read the query database, which keeps queries for
                91 days by default, rather than the last 24 hours in memory.
            count: How many queries to return, from 1 to 10,000. 100 by
                default.
            start: How many matching queries to skip, for paging: `0` for the
                first page, then `count`, `2 * count` and so on, each with
                the first page's `cursor`.
            cursor: The `cursor` from the first page's response, so newer
                queries don't shift later pages. Leave it out for the first
                page.
        """
        ...

    @method.get("/suggestions")
    async def suggestions(self, count: Annotated[int, Query(ge=1)] = 30) -> QuerySuggestionsResponse:
        """Fetch values to filter the query log by.

        It lists the domains, clients and upstream servers seen most, and
        every record type, status, reply and DNSSEC status the query log uses.
        Use it to find the exact names before filtering the log. It changes
        nothing.

        Args:
            count: How many domains and clients to suggest, at least 1. 30 by
                default.
        """
        ...
