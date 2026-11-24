"""The Pi-hole clients."""

import ssl
from types import TracebackType
from typing import Any, cast

from clientx import AsyncClientX, ClientX
from httpx2 import URL, AsyncBaseTransport, BaseTransport

from gravitywell._auth import PiHoleAuth
from gravitywell._resources.dns import AsyncDns, Dns
from gravitywell._resources.domains import AsyncDomains, Domains
from gravitywell._resources.history import AsyncHistory, History
from gravitywell._resources.info import AsyncInfo, Info
from gravitywell._resources.queries import AsyncQueries, Queries
from gravitywell._resources.search import AsyncSearch, Search
from gravitywell._resources.stats import AsyncStats, Stats
from gravitywell._version import __version__

# httpx2's `__exit__` doesn't call `close()`, nor `__aexit__` `aclose()`, so
# the clients override all four to log out of a `PiHoleAuth` session.


class _BasePiHole[TransportT: BaseTransport | AsyncBaseTransport]:
    """The constructor `PiHole` and `AsyncPiHole` share, which requires `auth`.

    `TransportT` is the client's kind of transport, sync or async.
    """

    def __init__(
        self,
        base_url: URL | str,
        *,
        auth: PiHoleAuth,
        verify: ssl.SSLContext | bool = True,
        transport: TransportT | None = None,
    ) -> None:
        """Create a client for the Pi-hole at `base_url`.

        A client sends requests to the Pi-hole's REST API and turns the
        replies into Pydantic models. Its attributes group the endpoints by
        API area, such as `api.info`, and each endpoint returns a model of its
        whole response body, from `gravitywell.models`. A 4xx or 5xx response
        raises `httpx2.HTTPStatusError`.

        It's an `httpx2.Client`, or an `httpx2.AsyncClient` for `AsyncPiHole`,
        built with ClientX. It logs in on its first request and reuses that
        session. Close it when you're done, by leaving its `with` block or
        calling `close()` (`aclose()` when async), to log out: a Pi-hole
        allows only a few sessions at a time.

        Args:
            base_url: The Pi-hole's URL, such as `http://pi.hole`. The client
                sets its path to `/api`, where the REST API is, so
                `http://pi.hole/api` works too, and any other path is
                replaced.
            auth: Logs in to the Pi-hole and sends its session on requests.
                Closing the client logs out.
            verify: How to check the Pi-hole's HTTPS certificate: an
                `ssl.SSLContext` that trusts Pi-hole's self-signed one, or
                `False` to skip the check.
            transport: Sends the requests in place of the network, such as an
                `httpx2.MockTransport` in tests. `AsyncPiHole` takes an async
                one.
        """
        base_url = URL(base_url).copy_with(path="/api")
        # `super()` is `ClientX` or `AsyncClientX`, next in the subclass's MRO,
        # which pyright can't see from this class.
        cast("Any", super()).__init__(base_url, auth=auth, verify=verify, transport=transport)


class PiHole(_BasePiHole[BaseTransport], ClientX, user_agent=f"gravitywell/{__version__}"):
    """A client for a Pi-hole's v6 REST API.

    Closing the client logs out of its session.
    """

    domains = Domains()
    dns = Dns()
    history = History()
    info = Info()
    queries = Queries()
    search = Search()
    stats = Stats()

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


class AsyncPiHole(_BasePiHole[AsyncBaseTransport], AsyncClientX, user_agent=f"gravitywell/{__version__}"):
    """The async version of `PiHole`."""

    domains = AsyncDomains()
    dns = AsyncDns()
    history = AsyncHistory()
    info = AsyncInfo()
    queries = AsyncQueries()
    search = AsyncSearch()
    stats = AsyncStats()

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
