"""The Pi-hole clients."""

import ssl
from types import TracebackType
from typing import Annotated, Any, cast

from clientx import AsyncClientX, ClientX
from clientx.tools import tool
from httpx2 import URL, AsyncBaseTransport, BaseTransport
from pydantic import Field

from gravitywell import _insights
from gravitywell._auth import PiHoleAuth
from gravitywell._resources.action import Action, AsyncAction
from gravitywell._resources.auth import AsyncSessions, Sessions
from gravitywell._resources.clients import AsyncClients, Clients
from gravitywell._resources.config import AsyncConfig, Config
from gravitywell._resources.dhcp import AsyncDhcp, Dhcp
from gravitywell._resources.dns import AsyncDns, Dns
from gravitywell._resources.domains import AsyncDomains, Domains
from gravitywell._resources.groups import AsyncGroups, Groups
from gravitywell._resources.history import AsyncHistory, History
from gravitywell._resources.info import AsyncInfo, Info
from gravitywell._resources.lists import AsyncLists, Lists
from gravitywell._resources.logs import AsyncLogs, Logs
from gravitywell._resources.network import AsyncNetwork, Network
from gravitywell._resources.padd import AsyncPadd, Padd
from gravitywell._resources.queries import AsyncQueries, Queries
from gravitywell._resources.search import AsyncSearch, Search
from gravitywell._resources.stats import AsyncStats, Stats
from gravitywell._resources.teleporter import AsyncTeleporter, Teleporter
from gravitywell._version import __version__
from gravitywell.models import ClientExplanation, DomainExplanation, HealthReport

# httpx2's `__exit__` doesn't call `close()`, nor `__aexit__` `aclose()`, so
# the clients override all four to log out of a `PiHoleAuth` session.


# How many of a domain's or client's newest queries the explain tools include.
_Recent = Annotated[int, Field(ge=1, le=100)]


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
    action = Action()
    clients = Clients()
    config = Config()
    dhcp = Dhcp()
    dns = Dns()
    groups = Groups()
    history = History()
    info = Info()
    lists = Lists()
    logs = Logs()
    network = Network()
    padd = Padd()
    queries = Queries()
    search = Search()
    sessions = Sessions()
    stats = Stats()
    teleporter = Teleporter()

    @tool(read_only=True, idempotent=True, tags=["insights"])
    def explain_domain(self, domain: str, recent: _Recent = 10) -> DomainExplanation:
        """Explain what the Pi-hole does with a domain, and why, in one call.

        It gathers the blocking status, the allow and deny rules and the lists
        that match the domain, the names of their groups, and its newest
        queries, whose status says what the Pi-hole did. Use it to answer why a
        domain is blocked or allowed, rather than calling the search, groups and
        query log endpoints in turn. For each client, Pi-hole decides in this
        order, using only the rules and lists of the client's groups: an allow
        rule, exact or regex, lets the domain through; else an exact deny rule
        blocks it; else an allowlist lets it through; else a blocklist blocks
        it; else a regex deny rule blocks it. It changes nothing.

        Args:
            domain: The domain, such as `ads.example.com`.
            recent: How many of its newest queries to include, 1 to 100.
        """
        return _insights.explain_domain(
            domain,
            self.dns.blocking(),
            self.search.lists(domain),
            self.groups.list(),
            self.queries.log(domain=domain, count=recent),
        )

    @tool(read_only=True, idempotent=True, tags=["insights"])
    def explain_client(self, address: str, recent: _Recent = 10) -> ClientExplanation:
        """Explain who a client is, which groups it's in, and what it asked for.

        It gathers the device with the IP address from the Pi-hole's network
        table (its MAC address, maker, hostnames and activity), the client
        records that match it, the names of their groups, and its newest
        queries. Use it to identify a device seen in the query log or the top
        clients. A device's groups come from the first kind of client record
        that matches it, in this order: IP address or subnet, MAC address,
        hostname, interface; with none, it's in the Default group only. An
        address that isn't an IP address is refused. It changes nothing.

        Args:
            address: The client's IP address, such as `192.168.1.235`.
            recent: How many of its newest queries to include, 1 to 100.
        """
        _insights.check_address(address)
        return _insights.explain_client(
            address,
            self.network.devices(max_devices=_insights.MAX_DEVICES, max_addresses=_insights.MAX_ADDRESSES),
            self.clients.list(),
            self.groups.list(),
            self.queries.log(client_ip=address, count=recent),
        )

    @tool(read_only=True, idempotent=True, tags=["insights"])
    def check_health(self) -> HealthReport:
        """Check the Pi-hole's health in one call, and list what's wrong.

        Its `findings` name the problems in plain words, the most urgent first,
        and are empty when all is well: DNS not running, blocking off, empty or
        failed blocklists, problems the Pi-hole reported, an overheating CPU,
        high memory use or load, lists not downloaded yet, and updates
        available. The other fields hold the details. Use it to answer whether
        the Pi-hole is all right; the PADD summary shows activity rather than
        problems. It changes nothing.
        """
        return _insights.check_health(
            self.dns.blocking(),
            self.info.messages(),
            self.info.version(),
            self.lists.list(),
            self.padd.summary(),
        )

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
    action = AsyncAction()
    clients = AsyncClients()
    config = AsyncConfig()
    dhcp = AsyncDhcp()
    dns = AsyncDns()
    groups = AsyncGroups()
    history = AsyncHistory()
    info = AsyncInfo()
    lists = AsyncLists()
    logs = AsyncLogs()
    network = AsyncNetwork()
    padd = AsyncPadd()
    queries = AsyncQueries()
    search = AsyncSearch()
    sessions = AsyncSessions()
    stats = AsyncStats()
    teleporter = AsyncTeleporter()

    @tool(read_only=True, idempotent=True, tags=["insights"])
    async def explain_domain(self, domain: str, recent: _Recent = 10) -> DomainExplanation:
        """Explain what the Pi-hole does with a domain, and why, in one call.

        It gathers the blocking status, the allow and deny rules and the lists
        that match the domain, the names of their groups, and its newest
        queries, whose status says what the Pi-hole did. Use it to answer why a
        domain is blocked or allowed, rather than calling the search, groups and
        query log endpoints in turn. For each client, Pi-hole decides in this
        order, using only the rules and lists of the client's groups: an allow
        rule, exact or regex, lets the domain through; else an exact deny rule
        blocks it; else an allowlist lets it through; else a blocklist blocks
        it; else a regex deny rule blocks it. It changes nothing.

        Args:
            domain: The domain, such as `ads.example.com`.
            recent: How many of its newest queries to include, 1 to 100.
        """
        return _insights.explain_domain(
            domain,
            await self.dns.blocking(),
            await self.search.lists(domain),
            await self.groups.list(),
            await self.queries.log(domain=domain, count=recent),
        )

    @tool(read_only=True, idempotent=True, tags=["insights"])
    async def explain_client(self, address: str, recent: _Recent = 10) -> ClientExplanation:
        """Explain who a client is, which groups it's in, and what it asked for.

        It gathers the device with the IP address from the Pi-hole's network
        table (its MAC address, maker, hostnames and activity), the client
        records that match it, the names of their groups, and its newest
        queries. Use it to identify a device seen in the query log or the top
        clients. A device's groups come from the first kind of client record
        that matches it, in this order: IP address or subnet, MAC address,
        hostname, interface; with none, it's in the Default group only. An
        address that isn't an IP address is refused. It changes nothing.

        Args:
            address: The client's IP address, such as `192.168.1.235`.
            recent: How many of its newest queries to include, 1 to 100.
        """
        _insights.check_address(address)
        return _insights.explain_client(
            address,
            await self.network.devices(max_devices=_insights.MAX_DEVICES, max_addresses=_insights.MAX_ADDRESSES),
            await self.clients.list(),
            await self.groups.list(),
            await self.queries.log(client_ip=address, count=recent),
        )

    @tool(read_only=True, idempotent=True, tags=["insights"])
    async def check_health(self) -> HealthReport:
        """Check the Pi-hole's health in one call, and list what's wrong.

        Its `findings` name the problems in plain words, the most urgent first,
        and are empty when all is well: DNS not running, blocking off, empty or
        failed blocklists, problems the Pi-hole reported, an overheating CPU,
        high memory use or load, lists not downloaded yet, and updates
        available. The other fields hold the details. Use it to answer whether
        the Pi-hole is all right; the PADD summary shows activity rather than
        problems. It changes nothing.
        """
        return _insights.check_health(
            await self.dns.blocking(),
            await self.info.messages(),
            await self.info.version(),
            await self.lists.list(),
            await self.padd.summary(),
        )

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
