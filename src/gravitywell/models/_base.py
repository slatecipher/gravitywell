"""The base of every response body model, and what models share."""

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
