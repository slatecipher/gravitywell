"""Models for the information endpoints, under `/info`."""

from pydantic import BaseModel, Field

from gravitywell.models._base import BaseResponse


class LocalVersion(BaseModel):
    """A component as installed on the Pi-hole."""

    version: str | None = Field(description="Its version, such as `v6.1`, or `null` if the Pi-hole doesn't report one.")


class ComponentVersion(BaseModel):
    """A Pi-hole component's version, as installed, under `local`."""

    local: LocalVersion


class Versions(BaseModel):
    """The version of each component: core, web and FTL."""

    core: ComponentVersion
    web: ComponentVersion
    ftl: ComponentVersion


class VersionResponse(BaseResponse):
    """The Pi-hole's version report."""

    version: Versions
