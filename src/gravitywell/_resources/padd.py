"""The PADD endpoint, under `/padd`.

PADD is Pi-hole's terminal dashboard, and this endpoint its summary.
"""

from typing import Annotated

from clientx import AsyncResource, Query, Resource, method

from gravitywell.models import PaddResponse


class Padd(Resource, prefix="/padd"):
    """PADD's summary of the Pi-hole's state."""

    @method.get("")
    def summary(self, full: Annotated[bool, Query()] = False) -> PaddResponse:
        """Fetch a summary of the Pi-hole's state in one call, as PADD shows it.

        It gives the blocking status, the last 24 hours' queries, the top
        domain, blocked domain and client, the DNS cache, the machine's load,
        memory and temperature, and a digest of key settings. Use it for a
        quick look at how the Pi-hole is doing; the statistics, info and
        config endpoints give more detail on each. It changes nothing.

        Args:
            full: Whether to add the network interfaces, and the versions of
                the Pi-hole's components with the newest ones available.
        """
        ...


class AsyncPadd(AsyncResource, prefix="/padd"):
    """PADD's summary of the Pi-hole's state."""

    @method.get("")
    async def summary(self, full: Annotated[bool, Query()] = False) -> PaddResponse:
        """Fetch a summary of the Pi-hole's state in one call, as PADD shows it.

        It gives the blocking status, the last 24 hours' queries, the top
        domain, blocked domain and client, the DNS cache, the machine's load,
        memory and temperature, and a digest of key settings. Use it for a
        quick look at how the Pi-hole is doing; the statistics, info and
        config endpoints give more detail on each. It changes nothing.

        Args:
            full: Whether to add the network interfaces, and the versions of
                the Pi-hole's components with the newest ones available.
        """
        ...
