"""The Pi-hole clients."""

import ssl
from types import TracebackType
from typing import Any, cast

import httpx2
from clientx import AsyncClientX, ClientX

from gravitywell._auth import PiHoleAuth
from gravitywell._resources.info import AsyncInfo, Info
from gravitywell._version import __version__

# httpx2's `__exit__` doesn't call `close()`, nor `__aexit__` `aclose()`, so
# the clients override all four to log out of a `PiHoleAuth` session.


class _BasePiHole[TransportT: httpx2.BaseTransport | httpx2.AsyncBaseTransport]:
    """The constructor `PiHole` and `AsyncPiHole` share, which requires `auth`.

    `TransportT` is the client's kind of transport, sync or async.
    """

    def __init__(
        self,
        base_url: httpx2.URL | str,
        *,
        auth: PiHoleAuth,
        verify: ssl.SSLContext | bool = True,
        transport: TransportT | None = None,
    ) -> None:
        # `super()` is `ClientX` or `AsyncClientX`, next in the subclass's MRO,
        # which pyright can't see from this class.
        cast("Any", super()).__init__(base_url, auth=auth, verify=verify, transport=transport)


class PiHole(_BasePiHole[httpx2.BaseTransport], ClientX, user_agent=f"gravitywell/{__version__}"):
    """A client for a Pi-hole's v6 REST API.

    Pass the Pi-hole's URL, such as `http://pi.hole`, and a `PiHoleAuth` as
    `auth=`. For HTTPS with Pi-hole's self-signed certificate, pass `verify=`
    an `ssl.SSLContext` that trusts it. Closing the client logs out of its
    session.
    """

    info = Info()

    def close(self) -> None:
        try:
            self._log_out()
        finally:
            super().close()

    def __exit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: TracebackType | None = None,
    ) -> None:
        try:
            self._log_out()
        finally:
            super().__exit__(exc_type, exc_value, traceback)

    def _log_out(self) -> None:
        if isinstance(self.auth, PiHoleAuth):
            self.auth.log_out(self)


class AsyncPiHole(_BasePiHole[httpx2.AsyncBaseTransport], AsyncClientX, user_agent=f"gravitywell/{__version__}"):
    """The async version of `PiHole`."""

    info = AsyncInfo()

    async def aclose(self) -> None:
        try:
            await self._log_out()
        finally:
            await super().aclose()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: TracebackType | None = None,
    ) -> None:
        try:
            await self._log_out()
        finally:
            await super().__aexit__(exc_type, exc_value, traceback)

    async def _log_out(self) -> None:
        if isinstance(self.auth, PiHoleAuth):
            await self.auth.alog_out(self)
