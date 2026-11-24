"""Models for the query log endpoints, under `/queries`."""

from datetime import datetime
from typing import Annotated, Literal, cast

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

from gravitywell.models._base import QUERY_STATUSES, REPLY_TYPES, BaseResponse, zero_as_none

# The values the query log's filters take. Plain aliases, not `type`
# statements, so JSON schemas write the enums in place.
QueryStatus = Literal[
    "UNKNOWN",
    "GRAVITY",
    "FORWARDED",
    "CACHE",
    "REGEX",
    "DENYLIST",
    "EXTERNAL_BLOCKED_IP",
    "EXTERNAL_BLOCKED_NULL",
    "EXTERNAL_BLOCKED_NXRA",
    "GRAVITY_CNAME",
    "REGEX_CNAME",
    "DENYLIST_CNAME",
    "RETRIED",
    "RETRIED_DNSSEC",
    "IN_PROGRESS",
    "DBBUSY",
    "SPECIAL_DOMAIN",
    "CACHE_STALE",
    "EXTERNAL_BLOCKED_EDE15",
]
ReplyType = Literal[
    "UNKNOWN",
    "NODATA",
    "NXDOMAIN",
    "CNAME",
    "IP",
    "DOMAIN",
    "RRNAME",
    "SERVFAIL",
    "REFUSED",
    "NOTIMP",
    "OTHER",
    "DNSSEC",
    "NONE",
    "BLOB",
]
DnssecStatus = Literal["UNKNOWN", "SECURE", "INSECURE", "BOGUS", "ABANDONED", "TRUNCATED"]
_DNSSEC_STATUSES = "`SECURE`, `INSECURE`, `BOGUS`, `ABANDONED`, `TRUNCATED` or `UNKNOWN`"


def _no_extended_error(value: object) -> object:
    # Pi-hole sends an Extended DNS Error code of -1 for a reply without one.
    raw = value  # Narrowed below, so `value` stays an `object` for pyright.
    fields = cast("dict[str, object]", raw) if isinstance(raw, dict) else {}
    return None if fields.get("code") == -1 else value


class QueryClient(BaseModel):
    """The device that sent a query."""

    ip: str = Field(description="Its IP address, IPv4 or IPv6, such as `192.168.1.235`.")
    name: str | None = Field(description="Its hostname, such as `laptop.lan`, or `null` if the Pi-hole knows none.")


class QueryReply(BaseModel):
    """The Pi-hole's reply to a query."""

    type: str | None = Field(description="The kind of reply: " + REPLY_TYPES)
    time: float = Field(description="Seconds the reply took, such as `0.016`, or `0` if unknown.")


class ExtendedDnsError(BaseModel):
    """An Extended DNS Error (RFC 8914) that came with a reply."""

    code: int = Field(description="Its code, such as `15` for a blocked domain.")
    text: str | None = Field(description="What the code means, such as `Blocked`, if the Pi-hole knows it.")


class LoggedQuery(BaseModel):
    """One DNS query in the Pi-hole's query log."""

    id: int = Field(description="Its ID in the query log. Newer queries have higher IDs.")
    time: datetime = Field(description="When it arrived, in UTC.")
    type: str = Field(
        description="The record type it asked for, such as `A`, `AAAA` or `HTTPS`, or `TYPEnnn` for a type without "
        "a name of its own."
    )
    domain: str = Field(description="The domain it asked for.")
    cname: str | None = Field(
        description="The domain in its CNAME chain that was blocked, if deep CNAME inspection blocked it."
    )
    status: str | None = Field(description="What the Pi-hole did with it. " + QUERY_STATUSES)
    client: QueryClient
    dnssec: str | None = Field(description=f"Its DNSSEC status: {_DNSSEC_STATUSES}.")
    reply: QueryReply
    upstream: str | None = Field(
        description="The upstream server that answered it, as `address#port`, such as `8.8.4.4#53`, or `null` if "
        "none did, as for a blocked or cached query."
    )
    rule_id: int | None = Field(description="The ID of the allow or deny rule that decided it, if one did.")
    list_id: int | None = Field(
        description="The ID of the subscribed blocklist or allowlist that decided it, if one did."
    )
    ede: Annotated[ExtendedDnsError | None, BeforeValidator(_no_extended_error)] = Field(
        description="The Extended DNS Error that came with the reply, or `null` if none did."
    )

    @model_validator(mode="before")
    @classmethod
    def _split_list_id(cls, data: object) -> object:
        # Pi-hole sends one `list_id`: -1 if nothing decided the query, the ID
        # of an allow or deny rule if one did, or for a subscribed list with
        # ID `n`, -2 - n. Split it so a model needn't decode it. Data with a
        # `rule_id`, such as a dumped `LoggedQuery`, is split already.
        body = data  # Narrowed below, so `data` stays an `object` for pyright.
        if not isinstance(body, dict) or "rule_id" in body:
            return data
        values = cast("dict[str, object]", body)
        raw = values.get("list_id")
        rule_id = raw if isinstance(raw, int) and raw >= 0 else None
        list_id = -2 - raw if isinstance(raw, int) and raw <= -2 else None
        return {**values, "rule_id": rule_id, "list_id": list_id}


class QueryLogResponse(BaseResponse):
    """A page of the Pi-hole's query log, newest first."""

    # Pi-hole's names, or the field names a dump or an AI tool's result uses.
    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)

    queries: list[LoggedQuery] = Field(description="Up to `count` queries that match the filters, newest first.")
    cursor: int | None = Field(
        description="The ID of the newest query this listing covers. To get the next page, pass it back as "
        "`cursor`, with `start` increased by `count`, so newer queries don't shift the pages. `null` if the privacy "
        "level hides queries."
    )
    records_total: int = Field(alias="recordsTotal", description="Queries in the log, or in the database with `disk`.")
    records_filtered: int = Field(
        alias="recordsFiltered",
        description="Queries that match the filters. More than `start` plus the queries returned means more pages.",
    )
    earliest_timestamp: Annotated[datetime | None, BeforeValidator(zero_as_none)] = Field(
        description="When the oldest query in memory arrived, in UTC, or `null` if there's none."
    )
    earliest_timestamp_disk: Annotated[datetime | None, BeforeValidator(zero_as_none)] = Field(
        description="When the oldest query in the database arrived, in UTC, as of the Pi-hole's start or its last "
        "cleanup of old queries, or `null` if it had none then, though it may have queries since. Read queries older "
        "than `earliest_timestamp` with `disk`."
    )


class QuerySuggestions(BaseModel):
    """Values to filter the query log by."""

    domain: list[str] = Field(description="The domains queried most, permitted and blocked.")
    client_ip: list[str] = Field(description="The IP addresses of the clients that sent the most queries.")
    client_name: list[str] = Field(description="The hostnames of the clients that sent the most queries.")
    upstream: list[str] = Field(
        description="The upstream servers, as `address#port (name)`, and `blocklist`, `cache` and `permitted`."
    )
    type: list[str] = Field(description="Every record type the log uses.")
    status: list[str] = Field(description="Every status the log uses.")
    reply: list[str] = Field(description="Every kind of reply the log uses.")
    dnssec: list[str] = Field(description="Every DNSSEC status the log uses.")


class QuerySuggestionsResponse(BaseResponse):
    """Values to filter the Pi-hole's query log by."""

    suggestions: QuerySuggestions
