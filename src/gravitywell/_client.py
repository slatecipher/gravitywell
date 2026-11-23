"""The Pi-hole clients."""

from clientx import AsyncClientX, ClientX

from gravitywell._resources.info import AsyncInfo, Info
from gravitywell._version import __version__


class PiHole(ClientX, user_agent=f"gravitywell/{__version__}"):
    """A client for a Pi-hole's v6 REST API.

    Pass the API's base URL, which ends in `/api`, such as
    `http://pi.hole/api`.
    """

    info = Info()


class AsyncPiHole(AsyncClientX, user_agent=f"gravitywell/{__version__}"):
    """The async version of `PiHole`."""

    info = AsyncInfo()
