"""The Pi-hole's information endpoints, under ``/info``."""

from clientx import AsyncResource, Resource, Response, method
from pydantic import BaseModel


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


def _versions(response: Response) -> Versions:
    # Pi-hole wraps them: {"version": {"core": ..., "web": ..., "ftl": ...}}.
    return Versions.model_validate(response.json()["version"])


class Info(Resource, prefix="/info"):
    """Information about the Pi-hole."""

    @method.get("/version", decoder=_versions)
    def version(self) -> Versions:
        """Fetch the installed versions of the Pi-hole's components."""
        ...


class AsyncInfo(AsyncResource, prefix="/info"):
    """Information about the Pi-hole."""

    @method.get("/version", decoder=_versions)
    async def version(self) -> Versions:
        """Fetch the installed versions of the Pi-hole's components."""
        ...
