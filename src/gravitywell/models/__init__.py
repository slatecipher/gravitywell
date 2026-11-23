"""The Pydantic models of the Pi-hole's request and response bodies.

Example:
    from gravitywell import PiHole
    from gravitywell.models import VersionResponse

    with PiHole("http://pi.hole/api") as api:
        body: VersionResponse = api.info.version()
"""

from gravitywell.models._base import BaseResponse
from gravitywell.models._info import ComponentVersion, LocalVersion, VersionResponse, Versions

__all__ = [
    # gravitywell.models._base
    "BaseResponse",
    # gravitywell.models._info
    "ComponentVersion",
    "LocalVersion",
    "VersionResponse",
    "Versions",
]
