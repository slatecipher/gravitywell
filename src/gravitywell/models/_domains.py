"""Models for the domain management endpoints, under `/domains`."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from gravitywell.models._base import GROUP_IDS, BaseResponse

# What a rule does, and what it matches. Plain aliases, not `type` statements,
# so JSON schemas write the enums in place.
RuleType = Literal["allow", "deny"]
RuleKind = Literal["exact", "regex"]


class DomainRule(BaseModel):
    """An allow or deny rule for domains: an exact domain, or a regex."""

    domain: str = Field(
        description="The domain, such as `ads.example.com`, or for a regex rule the regex, such as "
        "`(\\.|^)example\\.com$`."
    )
    unicode: str | None = Field(
        default=None,
        description="The domain in Unicode, such as `bücher.example` for `xn--bcher-kva.example`. The domain "
        "management endpoints send it; searches don't.",
    )
    type: RuleType = Field(description="`allow` lets matching domains through, `deny` blocks them.")
    kind: RuleKind = Field(description="`exact` matches that domain alone, `regex` every domain the regex matches.")
    comment: str | None = Field(description="The rule's comment, if any.")
    enabled: bool = Field(description="Whether the rule is in effect.")
    id: int = Field(description="The rule's ID in the Pi-hole's database.")
    groups: list[int] = Field(description=GROUP_IDS)
    date_added: datetime = Field(description="When the rule was added, in UTC.")
    date_modified: datetime = Field(description="When the rule was last changed, in UTC.")


class DomainRuleKey(BaseModel):
    """Which rule to delete: its domain or regex, type and kind."""

    domain: str = Field(serialization_alias="item", description="The rule's domain, or its regex, as `list` shows it.")
    type: RuleType = Field(description="The rule's type: `allow` or `deny`.")
    kind: RuleKind = Field(description="The rule's kind: `exact` or `regex`.")


class ProcessedItem(BaseModel):
    """An item a write saved."""

    item: str = Field(description="The item, such as a domain.")


class ProcessingError(BaseModel):
    """An item a write couldn't save, and why."""

    item: str = Field(description="The item, such as a domain.")
    error: str = Field(description="Why, such as `The item is already present`.")


class ProcessedItems(BaseModel):
    """Which items a write saved, and which it couldn't."""

    success: list[ProcessedItem] = Field(description="The items saved.")
    errors: list[ProcessingError] = Field(description="The items not saved, with the reason for each.")


class DomainsResponse(BaseResponse):
    """The Pi-hole's allow and deny rules."""

    domains: list[DomainRule] = Field(description="The rules.")


class ChangedDomainsResponse(BaseResponse):
    """A rule after a change, and which domains the change saved."""

    domains: list[DomainRule] = Field(
        description="The rule as it is now. When several domains were added, the last of them."
    )
    processed: ProcessedItems | None = Field(description="Which domains were saved, and which weren't and why.")
