"""The statistics endpoints, under `/stats`."""

from clientx import AsyncResource, Resource, method

from gravitywell.models import SummaryResponse


class Stats(Resource, prefix="/stats"):
    """Statistics about the Pi-hole's activity."""

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


class AsyncStats(AsyncResource, prefix="/stats"):
    """Statistics about the Pi-hole's activity."""

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
