"""Models for the group management endpoints, under `/groups`."""

from datetime import datetime

from pydantic import BaseModel, Field

from gravitywell.models._base import BaseResponse, ProcessedItems


class Group(BaseModel):
    """A group of clients, which rules and lists apply to."""

    name: str = Field(
        description="The group's name, such as `Kids`. `Default`, ID `0`, holds every client the Pi-hole doesn't "
        "know, and gets every new rule, list and client."
    )
    comment: str | None = Field(description="The group's comment, if any.")
    enabled: bool = Field(
        description="Whether the group is in effect. A disabled group's rules and lists don't apply to its clients "
        "through it."
    )
    id: int = Field(description="The group's ID, as the `groups` of rules, lists and clients show it.")
    date_added: datetime = Field(description="When the group was added, in UTC.")
    date_modified: datetime = Field(description="When the group last changed, in UTC.")


class GroupKey(BaseModel):
    """Which group to delete."""

    name: str = Field(serialization_alias="item", description="The group's name.")


class GroupsResponse(BaseResponse):
    """The Pi-hole's groups of clients."""

    groups: list[Group] = Field(description="The groups.")


class ChangedGroupsResponse(BaseResponse):
    """A group after a change, and which groups the change saved."""

    groups: list[Group] = Field(description="The group as it is now. When several groups were added, the last of them.")
    processed: ProcessedItems | None = Field(description="Which groups were saved, and which weren't and why.")
