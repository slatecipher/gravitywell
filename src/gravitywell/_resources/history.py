"""The history endpoints, under `/history`."""

from typing import Annotated

from clientx import AsyncResource, Query, Resource, method

from gravitywell.models import (
    ActivityResponse,
    ClientActivityResponse,
    DatabaseActivityResponse,
    DatabaseClientActivityResponse,
    TimeRange,
)


class HistoryDatabase(Resource, prefix="/history/database"):
    """Query counts over time, from the Pi-hole's query database."""

    @method.get()
    def activity(self, time_range: Annotated[TimeRange, Query()]) -> DatabaseActivityResponse:
        """Fetch the Pi-hole's query counts over a time range.

        It reads the query database, which keeps queries for 91 days by
        default, in 10-minute slots: total, cached, blocked and forwarded,
        leaving out slots without queries. Use it for activity older than the
        last 24 hours. A day has up to 144 slots, so keep long ranges for
        questions that need them. It changes nothing.

        Args:
            time_range: The range to cover: `start`, and `until`, now by
                default, both with a timezone.
        """
        ...

    @method.get("/clients")
    def clients(self, time_range: Annotated[TimeRange, Query()]) -> DatabaseClientActivityResponse:
        """Fetch each client's query counts over a time range.

        It reads the query database, which keeps queries for 91 days by
        default, in 10-minute slots, and lists every client that sent a query
        in the range. A day has up to 144 slots, so keep long ranges for
        questions that need them. It changes nothing.

        Args:
            time_range: The range to cover: `start`, and `until`, now by
                default, both with a timezone.
        """
        ...


class History(Resource, prefix="/history"):
    """Query counts over time, in 10-minute slots."""

    database = HistoryDatabase()

    @method.get()
    def activity(self) -> ActivityResponse:
        """Fetch the Pi-hole's query counts over the last 24 hours.

        Each 10-minute slot counts its queries: total, cached, blocked and
        forwarded, the data behind the dashboard's activity graph. Use it to
        see when queries happened, such as a burst of blocked queries in the
        night; for totals alone, the stats summary is shorter. It changes
        nothing.
        """
        ...

    @method.get("/clients")
    def clients(self, count: Annotated[int | None, Query(alias="N", ge=0)] = None) -> ClientActivityResponse:
        """Fetch each client's query counts over the last 24 hours.

        Each 10-minute slot counts the queries of the clients with the most
        queries, and sums the rest under `others`. Use it to see which device
        was active when. The lists are empty if the Pi-hole's privacy level
        hides clients. It changes nothing.

        Args:
            count: The most clients to list, `others` included: with more
                clients than that, the top `count - 1` are listed and the rest
                summed under `others`. `0` lists every client. Leave it out
                for the Pi-hole's setting, 10 by default.
        """
        ...


class AsyncHistoryDatabase(AsyncResource, prefix="/history/database"):
    """Query counts over time, from the Pi-hole's query database."""

    @method.get()
    async def activity(self, time_range: Annotated[TimeRange, Query()]) -> DatabaseActivityResponse:
        """Fetch the Pi-hole's query counts over a time range.

        It reads the query database, which keeps queries for 91 days by
        default, in 10-minute slots: total, cached, blocked and forwarded,
        leaving out slots without queries. Use it for activity older than the
        last 24 hours. A day has up to 144 slots, so keep long ranges for
        questions that need them. It changes nothing.

        Args:
            time_range: The range to cover: `start`, and `until`, now by
                default, both with a timezone.
        """
        ...

    @method.get("/clients")
    async def clients(self, time_range: Annotated[TimeRange, Query()]) -> DatabaseClientActivityResponse:
        """Fetch each client's query counts over a time range.

        It reads the query database, which keeps queries for 91 days by
        default, in 10-minute slots, and lists every client that sent a query
        in the range. A day has up to 144 slots, so keep long ranges for
        questions that need them. It changes nothing.

        Args:
            time_range: The range to cover: `start`, and `until`, now by
                default, both with a timezone.
        """
        ...


class AsyncHistory(AsyncResource, prefix="/history"):
    """Query counts over time, in 10-minute slots."""

    database = AsyncHistoryDatabase()

    @method.get()
    async def activity(self) -> ActivityResponse:
        """Fetch the Pi-hole's query counts over the last 24 hours.

        Each 10-minute slot counts its queries: total, cached, blocked and
        forwarded, the data behind the dashboard's activity graph. Use it to
        see when queries happened, such as a burst of blocked queries in the
        night; for totals alone, the stats summary is shorter. It changes
        nothing.
        """
        ...

    @method.get("/clients")
    async def clients(self, count: Annotated[int | None, Query(alias="N", ge=0)] = None) -> ClientActivityResponse:
        """Fetch each client's query counts over the last 24 hours.

        Each 10-minute slot counts the queries of the clients with the most
        queries, and sums the rest under `others`. Use it to see which device
        was active when. The lists are empty if the Pi-hole's privacy level
        hides clients. It changes nothing.

        Args:
            count: The most clients to list, `others` included: with more
                clients than that, the top `count - 1` are listed and the rest
                summed under `others`. `0` lists every client. Leave it out
                for the Pi-hole's setting, 10 by default.
        """
        ...
