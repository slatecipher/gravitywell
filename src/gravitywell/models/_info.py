"""Models for the information endpoints, under ``/info``."""

from pydantic import BaseModel

from gravitywell.models._base import BaseResponse


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
