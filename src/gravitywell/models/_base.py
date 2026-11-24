"""The base of every response body model, and what models share."""

from typing import Literal

from pydantic import BaseModel, Field

# What the Pi-hole did with a query, and the kinds of reply: the stats summary
# counts them, and the query log shows them for each query.
QUERY_STATUSES = (
    "Blocked: `GRAVITY` (on a blocklist), `REGEX` and `DENYLIST` (by a domain rule), `GRAVITY_CNAME`, `REGEX_CNAME` "
    "and `DENYLIST_CNAME` (the same, found in a CNAME chain), `EXTERNAL_BLOCKED_IP`, `EXTERNAL_BLOCKED_NULL`, "
    "`EXTERNAL_BLOCKED_NXRA` and `EXTERNAL_BLOCKED_EDE15` (blocked by the upstream server), `SPECIAL_DOMAIN` and "
    "`DBBUSY` (the blocklist database was busy). Not blocked: `FORWARDED`, `CACHE`, `CACHE_STALE`, `RETRIED`, "
    "`RETRIED_DNSSEC`, `IN_PROGRESS` and `UNKNOWN`."
)
REPLY_TYPES = (
    "`IP` (an address), `NXDOMAIN` (no such domain), `NODATA` (no record of that type), `CNAME`, `DOMAIN` (a name, "
    "such as a reverse lookup's), `BLOB` (other record data, such as a `TXT`, `MX` or `HTTPS` answer), `SERVFAIL`, "
    "`REFUSED`, `NOTIMP`, `DNSSEC`, `RRNAME`, `OTHER`, `NONE` (not answered yet) and `UNKNOWN`."
)

# Whether the Pi-hole is blocking: the blocking endpoint and PADD's summary
# report it. FTL sends `failure`, though its API spec says `failed`: accept
# both.
BlockingStatus = Literal["enabled", "disabled", "failure", "failed", "unknown"]
BLOCKING_STATUS = (
    "The status: `enabled` (blocking), `disabled` (letting every domain through), `failure` (the DNS server isn't "
    "running, so nothing is answered; the API's spec calls it `failed`) or `unknown` (not known yet, such as while "
    "the Pi-hole starts)."
)

# The groups a rule, list or client belongs to.
GROUP_IDS = (
    "IDs of the groups it applies to: it affects only clients in those groups. `0` is the Default group, which every "
    "client is in unless moved."
)


def zero_as_none(value: object) -> object:
    """Read the `0` Pi-hole sends for a time it doesn't know as `None`."""
    return None if value == 0 else value


class BaseResponse(BaseModel):
    """The fields every Pi-hole response body has."""

    took: float = Field(description="Seconds the Pi-hole took to process the request.")


class ProcessedItem(BaseModel):
    """An item a write saved."""

    item: str = Field(description="The item, such as a domain or a list's URL.")


class ProcessingError(BaseModel):
    """An item a write couldn't save, and why."""

    item: str = Field(description="The item, such as a domain or a list's URL.")
    error: str = Field(description="Why, such as `The item is already present`.")


class ProcessedItems(BaseModel):
    """Which items a write saved, and which it couldn't."""

    success: list[ProcessedItem] = Field(description="The items saved.")
    errors: list[ProcessingError] = Field(description="The items not saved, with the reason for each.")
