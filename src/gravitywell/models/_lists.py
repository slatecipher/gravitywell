"""Models for the list management endpoints, under `/lists`."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, Field

from gravitywell.models._base import GROUP_IDS, BaseResponse, ProcessedItems, zero_as_none

# Whether a list blocks or allows its domains. A plain alias, not a `type`
# statement, so JSON schemas write the enum in place.
ListType = Literal["block", "allow"]


class SubscribedList(BaseModel):
    """A blocklist or allowlist the Pi-hole subscribes to, by its URL."""

    address: str = Field(
        description="The list's URL, such as `https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts`."
    )
    type: ListType = Field(
        description="`block` for a blocklist, whose domains are blocked; `allow` for an allowlist, whose domains are "
        "let through even when a blocklist has them."
    )
    comment: str | None = Field(description="The list's comment, if any.")
    groups: list[int] = Field(description=GROUP_IDS)
    enabled: bool = Field(description="Whether the list is in effect. Gravity updates download only enabled lists.")
    id: int = Field(description="The list's ID in the Pi-hole's database, as a logged query's `list_id` shows it.")
    date_added: datetime = Field(description="When the list was added, in UTC.")
    date_modified: datetime = Field(description="When the list's settings last changed, in UTC.")
    date_updated: Annotated[datetime | None, BeforeValidator(zero_as_none)] = Field(
        description="When the Pi-hole last updated its copy of the list, in a gravity update, in UTC, or `null` if "
        "it never has."
    )
    number: int = Field(description="Domains on the list, as of the last gravity update.")
    invalid_domains: int = Field(description="Lines on the list the Pi-hole couldn't read as domains.")
    abp_entries: int = Field(description="Entries in ABP style, such as `||example.com^`, which also cover subdomains.")
    status: int = Field(
        description="The last gravity update's result: `0` not downloaded yet, `1` downloaded, `2` unchanged "
        "upstream so the local copy was used, `3` unavailable so the local copy was used, `4` unavailable with no "
        "local copy."
    )


class ListKey(BaseModel):
    """Which list to delete: its URL and type."""

    address: str = Field(serialization_alias="item", description="The list's URL.")
    type: ListType = Field(description="The list's type: `block` or `allow`.")


class ListsResponse(BaseResponse):
    """The blocklists and allowlists the Pi-hole subscribes to."""

    lists: list[SubscribedList] = Field(description="The lists.")


class ChangedListsResponse(BaseResponse):
    """A list after a change, and which lists the change saved."""

    lists: list[SubscribedList] = Field(
        description="The list as it is now. When several lists were added, the last of them."
    )
    processed: ProcessedItems | None = Field(description="Which lists were saved, and which weren't and why.")
