"""The information endpoints, under ``/info``."""

from clientx import AsyncResource, Resource, method

from gravitywell.models import VersionResponse


class Info(Resource, prefix="/info"):
    """Information about the Pi-hole."""

    @method.get("/version")
    def version(self) -> VersionResponse:
        """Fetch the installed versions of the Pi-hole's components."""
        ...


class AsyncInfo(AsyncResource, prefix="/info"):
    """Information about the Pi-hole."""

    @method.get("/version")
    async def version(self) -> VersionResponse:
        """Fetch the installed versions of the Pi-hole's components."""
        ...
