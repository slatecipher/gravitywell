"""The Pi-hole's information endpoints, under ``/info``."""

from clientx import AsyncResource, Resource, method
from pydantic import BaseModel

from gravitywell._response import BaseResponse


class LocalVersion(BaseModel):
    """The version of a component installed on the Pi-hole."""

    version: str | None


class ComponentVersion(BaseModel):
    """The versions of one Pi-hole component."""

    local: LocalVersion


class Versions(BaseModel):
    """The versions of the Pi-hole's components."""

    core: ComponentVersion
    web: ComponentVersion
    ftl: ComponentVersion


class VersionResponse(BaseResponse):
    """The body of ``GET /info/version``."""

    version: Versions


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
