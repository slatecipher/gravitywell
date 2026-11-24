"""Models for the statistics endpoints, under `/stats`."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, Field

from gravitywell.models._base import BaseResponse


def _zero_is_none(value: object) -> object:
    # Pi-hole sends a Unix time of 0 when it doesn't know the time.
    return None if value == 0 else value


def _minus_one_is_none(value: object) -> object:
    # Pi-hole sends a total of -1 when its privacy level hides the list.
    return None if value == -1 else value


# A plain alias, not a `type` statement, so JSON schemas write it in place.
_HiddenTotal = Annotated[int | None, BeforeValidator(_minus_one_is_none)]

_QUERY_TYPES = (
    "Queries by record type: `A`, `AAAA`, `ANY`, `SRV`, `SOA`, `PTR`, `TXT`, `NAPTR`, `MX`, `DS`, `RRSIG`, "
    "`DNSKEY`, `NS`, `SVCB`, `HTTPS`, and `OTHER` for the rest."
)


class QuerySummary(BaseModel):
    """DNS queries in the Pi-hole's history, the last 24 hours by default."""

    total: int = Field(description="Queries received.")
    blocked: int = Field(description="Queries blocked, which the statuses in `status` marked as blocked add up to.")
    percent_blocked: float = Field(description="Share of queries blocked, in percent from 0 to 100, such as `34.5`.")
    unique_domains: int = Field(description="Different domains queried.")
    forwarded: int = Field(description="Queries answered by an upstream DNS server.")
    cached: int = Field(description="Queries answered from the cache or the Pi-hole's own configuration.")
    frequency: float = Field(description="Queries per second, averaged over the last 30 seconds.")
    types: dict[str, int] = Field(description=_QUERY_TYPES)
    status: dict[str, int] = Field(
        description="Queries by what the Pi-hole did with them. Blocked: `GRAVITY` (on a blocklist), `REGEX` and "
        "`DENYLIST` (by a domain rule), `GRAVITY_CNAME`, `REGEX_CNAME` and `DENYLIST_CNAME` (the same, found in a "
        "CNAME chain), `EXTERNAL_BLOCKED_IP`, `EXTERNAL_BLOCKED_NULL`, `EXTERNAL_BLOCKED_NXRA` and "
        "`EXTERNAL_BLOCKED_EDE15` (blocked by the upstream server), `SPECIAL_DOMAIN` and `DBBUSY` (the blocklist "
        "database was busy). Not blocked: `FORWARDED`, `CACHE`, `CACHE_STALE`, `RETRIED`, `RETRIED_DNSSEC`, "
        "`IN_PROGRESS` and `UNKNOWN`."
    )
    replies: dict[str, int] = Field(
        description="Replies by kind: `IP` (an address), `NXDOMAIN` (no such domain), `NODATA` (no record of that "
        "type), `CNAME`, `DOMAIN` (a name, such as a reverse lookup's), `BLOB` (other record data, such as a `TXT`, "
        "`MX` or `HTTPS` answer), `SERVFAIL`, `REFUSED`, `NOTIMP`, `DNSSEC`, `RRNAME`, `OTHER`, `NONE` (not answered "
        "yet) and `UNKNOWN`."
    )


class ClientSummary(BaseModel):
    """The devices that send the Pi-hole DNS queries."""

    active: int = Field(description="Clients that sent a query in the last 24 hours.")
    total: int = Field(description="Clients the Pi-hole knows, active or not.")


class GravitySummary(BaseModel):
    """The Pi-hole's blocklists, combined into its gravity database."""

    domains_being_blocked: int = Field(description="Domains on the blocklists.")
    last_update: Annotated[datetime | None, BeforeValidator(_zero_is_none)] = Field(
        description="When the blocklists were last updated, in UTC, or `null` if the Pi-hole doesn't know."
    )


class SummaryResponse(BaseResponse):
    """An overview of the Pi-hole's queries, clients and blocklists."""

    queries: QuerySummary
    clients: ClientSummary
    gravity: GravitySummary


class TopDomain(BaseModel):
    """A domain, and how many queries asked for it."""

    domain: str = Field(description="The domain, such as `pi-hole.net`.")
    count: int = Field(description="Queries for it, of the kind asked for: permitted or blocked.")


class TopDomainsResponse(BaseResponse):
    """The domains queried most, permitted or blocked, most queries first."""

    domains: list[TopDomain] = Field(
        description="Up to `count` domains, most queries first. Empty if the Pi-hole's privacy level hides domains."
    )
    total_queries: _HiddenTotal = Field(
        description="All queries in the Pi-hole's history, or `null` if its privacy level hides domains."
    )
    blocked_queries: _HiddenTotal = Field(
        description="Blocked queries in the Pi-hole's history, or `null` if its privacy level hides domains."
    )


class TopClient(BaseModel):
    """A device that queries the Pi-hole, and how many queries it sent."""

    ip: str = Field(description="Its IP address, IPv4 or IPv6, such as `192.168.0.44`.")
    name: str = Field(description="Its hostname, such as `laptop.lan`, or an empty string if the Pi-hole knows none.")
    count: int = Field(description="Its queries, of the kind asked for: all of them, or only the blocked ones.")


class TopClientsResponse(BaseResponse):
    """The clients that sent the most queries, most queries first."""

    clients: list[TopClient] = Field(
        description="Up to `count` clients, most queries first. Empty if the Pi-hole's privacy level hides clients."
    )
    total_queries: _HiddenTotal = Field(
        description="All queries in the Pi-hole's history, or `null` if its privacy level hides clients."
    )
    blocked_queries: _HiddenTotal = Field(
        description="Blocked queries in the Pi-hole's history, or `null` if its privacy level hides clients."
    )


class QueryTypesResponse(BaseResponse):
    """The Pi-hole's queries by DNS record type."""

    types: dict[str, int] = Field(description=_QUERY_TYPES)


class UpstreamStatistics(BaseModel):
    """How fast an upstream DNS server answers."""

    response: float = Field(
        description="Average response time, in seconds, such as `0.016`. `0` for `blocklist` and `cache`, and for a "
        "server with no replies yet."
    )
    variance: float = Field(
        description="Despite its name, the uncertainty of `response` (its standard error), in seconds. `0` for "
        "`blocklist` and `cache`, and for a server with fewer than two replies."
    )


class Upstream(BaseModel):
    """Where the Pi-hole sent queries, and how many."""

    ip: str | None = Field(
        description="The upstream DNS server's IP address, such as `8.8.4.4`, or `blocklist` for the queries the "
        "Pi-hole blocked and `cache` for those it answered from its cache."
    )
    name: str | None = Field(
        description="The server's hostname, such as `dns.google`, if known; `blocklist` or `cache` for those entries."
    )
    port: int = Field(description="The server's port, such as `53`, or `-1` for `blocklist` and `cache`.")
    count: int = Field(description="Queries it handled.")
    statistics: UpstreamStatistics


class UpstreamsResponse(BaseResponse):
    """Where the Pi-hole's queries went: blocked, cached, or to which server."""

    upstreams: list[Upstream] = Field(
        description="`blocklist` and `cache` first, then each upstream server that answered a query, most queries "
        "first."
    )
    forwarded_queries: int = Field(description="Queries answered by an upstream server.")
    total_queries: int = Field(description="All queries in the Pi-hole's history.")


class RecentBlockedResponse(BaseResponse):
    """The domains the Pi-hole blocked most recently."""

    blocked: list[str] = Field(
        description="Up to `count` blocked domains, most recent first, once per query, so a domain can appear more "
        "than once. `hidden` stands for a domain the privacy level hid when it was queried, and the list is empty if "
        "the privacy level hides domains."
    )
