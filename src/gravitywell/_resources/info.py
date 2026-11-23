"""The information endpoints, under `/info`."""

from clientx import AsyncResource, Resource, method

from gravitywell.models import VersionResponse


class Info(Resource, prefix="/info"):
    """Information about the Pi-hole."""

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
    """Information about the Pi-hole."""

    @method.get("/version")
    async def version(self) -> VersionResponse:
        """Fetch the installed versions of the Pi-hole's components.

        Pi-hole has three: core (its scripts and the `pihole` command), web
        (the web interface) and FTL (the DNS server, which also serves this
        API). Use it to check which Pi-hole release runs, such as before
        reporting a problem.
        """
        ...
