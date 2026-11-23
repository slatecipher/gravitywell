"""A third-party, typed client for the Pi-hole v6 REST API.

Example:
    from gravitywell import PiHole

    with PiHole("http://pi.hole/api") as api:
        print(api.info.version().version.ftl.local.version)
"""

from gravitywell._client import AsyncPiHole, PiHole
from gravitywell._info import ComponentVersion, LocalVersion, VersionResponse, Versions
from gravitywell._version import __version__

__all__ = [
    # gravitywell._version
    "__version__",
    # gravitywell._client
    "AsyncPiHole",
    "PiHole",
    # gravitywell._info
    "ComponentVersion",
    "LocalVersion",
    "VersionResponse",
    "Versions",
]
