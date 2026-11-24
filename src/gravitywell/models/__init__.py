"""The Pydantic models of the Pi-hole's request and response bodies.

Example:
    import os

    from gravitywell import PiHole, PiHoleAuth
    from gravitywell.models import VersionResponse

    auth = PiHoleAuth(os.environ["PIHOLE_PASSWORD"])
    with PiHole("http://pi.hole", auth=auth) as api:
        body: VersionResponse = api.info.version()
"""

from gravitywell.models._auth import Session, SessionResponse
from gravitywell.models._base import BaseResponse
from gravitywell.models._dns import BlockingResponse
from gravitywell.models._info import ComponentVersion, LocalVersion, VersionResponse, Versions
from gravitywell.models._stats import (
    ClientSummary,
    GravitySummary,
    QuerySummary,
    SummaryResponse,
    TopClient,
    TopClientsResponse,
    TopDomain,
    TopDomainsResponse,
)

__all__ = [
    # gravitywell.models._auth
    "Session",
    "SessionResponse",
    # gravitywell.models._base
    "BaseResponse",
    # gravitywell.models._dns
    "BlockingResponse",
    # gravitywell.models._info
    "ComponentVersion",
    "LocalVersion",
    "VersionResponse",
    "Versions",
    # gravitywell.models._stats
    "ClientSummary",
    "GravitySummary",
    "QuerySummary",
    "SummaryResponse",
    "TopClient",
    "TopClientsResponse",
    "TopDomain",
    "TopDomainsResponse",
]
