"""Models for the search endpoint, under `/search`."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from gravitywell.models._base import BaseResponse

_GROUPS = (
    "IDs of the groups it applies to: it affects only clients in those groups. `0` is the Default group, which every "
    "client is in unless moved."
)


class DomainRule(BaseModel):
    """An allow or deny rule for domains: an exact domain, or a regex."""

    domain: str = Field(
        description="The domain, such as `ads.example.com`, or for a regex rule the regex, such as "
        "`(\\.|^)example\\.com$`."
    )
    type: Literal["allow", "deny"] = Field(description="`allow` lets matching domains through, `deny` blocks them.")
    kind: Literal["exact", "regex"] = Field(
        description="`exact` matches that domain alone, `regex` every domain the regex matches."
    )
    comment: str | None = Field(description="The rule's comment, if any.")
    enabled: bool = Field(description="Whether the rule is in effect.")
    id: int = Field(description="The rule's ID in the Pi-hole's database.")
    groups: list[int] = Field(description=_GROUPS)
    date_added: datetime = Field(description="When the rule was added, in UTC.")
    date_modified: datetime = Field(description="When the rule was last changed, in UTC.")


class ListMatch(BaseModel):
    """An entry on a subscribed blocklist or allowlist that matches a domain."""

    domain: str = Field(
        description="The entry that matched: the domain, or a parent domain in ABP style, such as `||example.com^`."
    )
    type: Literal["block", "allow"] = Field(description="`block` for a blocklist, `allow` for an allowlist.")
    address: str = Field(
        description="The list's URL, such as `https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts`."
    )
    comment: str | None = Field(description="The list's comment, if any.")
    enabled: bool = Field(description="Whether the list is in effect.")
    id: int = Field(description="The list's ID in the Pi-hole's database.")
    groups: list[int] = Field(description=_GROUPS)


class RuleMatchCounts(BaseModel):
    """How many allow and deny rules match, by kind."""

    exact: int = Field(description="Exact rules that match.")
    regex: int = Field(description="Regex rules that match.")


class ListMatchCounts(BaseModel):
    """How many list entries match, by type of list."""

    allow: int = Field(description="Allowlist entries that match.")
    block: int = Field(description="Blocklist entries that match.")


class SearchCounts(BaseModel):
    """How many matches there are, including any beyond `count`."""

    domains: RuleMatchCounts
    gravity: ListMatchCounts
    total: int = Field(description="All matches.")


class SearchResults(BaseModel):
    """The rules and list entries that match a domain."""

    domains: list[DomainRule] = Field(description="Allow and deny rules that match, up to `count` of each kind.")
    gravity: list[ListMatch] = Field(
        description="Blocklist and allowlist entries that match, up to `count` of each type."
    )
    results: SearchCounts


class SearchResponse(BaseResponse):
    """The Pi-hole's rules and list entries that match a domain."""

    search: SearchResults
