"""A third-party, typed client for the Pi-hole v6 REST API.

The models of request and response bodies are in ``gravitywell.models``.

Example:
    from gravitywell import PiHole

    with PiHole("http://pi.hole/api") as api:
        print(api.info.version().version.ftl.local.version)
"""

from gravitywell._client import AsyncPiHole, PiHole
from gravitywell._version import __version__

__all__ = [
    # gravitywell._version
    "__version__",
    # gravitywell._client
    "AsyncPiHole",
    "PiHole",
]
