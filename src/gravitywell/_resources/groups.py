"""The group management endpoints, under `/groups`."""

from typing import Annotated

from clientx import AsyncResource, Json, Resource, method
from clientx.tools import ToolOptions

from gravitywell.models import ChangedGroupsResponse, GroupKey, GroupsResponse

# A POST, so AI tools would treat it as neither: it deletes, and deleting the
# same groups again changes nothing more.
_BATCH_DELETE = ToolOptions(destructive=True, idempotent=True)


class GroupsBatch(Resource):
    """Change several groups at once."""

    # The full path: ClientX joins a prefix and `:batchDelete` with a slash
    # (ClientX #173).
    @method.post("/groups:batchDelete", tool_options=_BATCH_DELETE)
    def delete(self, groups: Annotated[list[GroupKey], Json()]) -> None:
        """Delete several groups at once.

        Their rules, lists and clients stay, but no longer belong to them.
        Don't delete the Default group, ID `0`: Pi-hole re-creates it, but
        empty, so every rule, list and client in it stops applying until it's
        added back. Groups that don't exist are skipped, but if none of them
        exists, it answers with an error (404).

        Args:
            groups: The groups to delete, each by its name.
        """
        ...


class Groups(Resource, prefix="/groups"):
    """The Pi-hole's groups of clients, which rules and lists apply to."""

    batch = GroupsBatch()

    @method.get("/{name}")
    def get(self, name: str) -> GroupsResponse:
        """Fetch one group by its name.

        It returns the group in a list, or an empty list if there's no such
        group. It changes nothing.

        Args:
            name: The group's name, such as `Kids`.
        """
        ...

    @method.post()
    def add(
        self,
        name: Annotated[str | list[str], Json()],
        comment: Annotated[str | None, Json()] = None,
        enabled: Annotated[bool, Json()] = True,
    ) -> ChangedGroupsResponse:
        """Add one or more groups.

        A new group has no clients, rules or lists: give it some through
        their `groups`. Each name is saved or refused on its own, such as one
        already taken, and `processed` says which; if all are refused, it
        answers with an error.

        Args:
            name: The group's name, or a list of names, such as `Kids`.
            comment: A note on the group, such as `Bedtime filtering`.
            enabled: `false` to add the group without putting it in effect.
        """
        ...

    @method.put("/{name}")
    def update(
        self,
        name: str,
        comment: Annotated[str | None, Json()] = None,
        enabled: Annotated[bool, Json()] = True,
    ) -> ChangedGroupsResponse:
        """Change a group's comment or state.

        It replaces the group's settings: a comment left out is removed, and
        `enabled` left out means enabled. If there's no such group, it adds
        one. To rename a group, use the rename endpoint. It takes effect
        right away.

        Args:
            name: The group's name, such as `Kids`.
            comment: The group's comment, such as `Bedtime filtering`. Leave
                it out to remove the current one.
            enabled: `false` to keep the group but take it out of effect.
        """
        ...

    # Pi-hole renames a group with a PUT whose body has the new name.
    @method.put("/{name}")
    def rename(
        self,
        name: str,
        new_name: Annotated[str, Json(alias="name")],
        comment: Annotated[str | None, Json()] = None,
        enabled: Annotated[bool, Json()] = True,
    ) -> ChangedGroupsResponse:
        """Rename a group.

        Its ID, clients, rules and lists stay. It also replaces the group's
        settings, as an update does: a comment left out is removed, and
        `enabled` left out means enabled. It takes effect right away.

        Args:
            name: The group's name now, such as `Kids`.
            new_name: The name to give it, such as `Children`.
            comment: The group's comment, such as `Bedtime filtering`. Leave
                it out to remove the current one.
            enabled: `false` to keep the group but take it out of effect.
        """
        ...

    @method.delete("/{name}")
    def delete(self, name: str) -> None:
        """Delete a group.

        Its rules, lists and clients stay, but no longer belong to it. Don't
        delete the Default group, ID `0`: Pi-hole re-creates it, but empty, so
        every rule, list and client in it stops applying until it's added
        back. A group that doesn't exist answers with an error (404).

        Args:
            name: The group's name, such as `Kids`.
        """
        ...

    # Last in the class: a method named `list` hides the builtin for the rest
    # of the class body.
    @method.get()
    def list(self) -> GroupsResponse:
        """Fetch the Pi-hole's groups of clients.

        Rules, lists and clients belong to groups by ID, and a rule or list
        applies to the clients in its groups. `Default`, ID `0`, holds every
        client the Pi-hole doesn't know, and gets every new rule, list and
        client. It changes nothing.
        """
        ...


class AsyncGroupsBatch(AsyncResource):
    """Change several groups at once."""

    # The full path: ClientX joins a prefix and `:batchDelete` with a slash
    # (ClientX #173).
    @method.post("/groups:batchDelete", tool_options=_BATCH_DELETE)
    async def delete(self, groups: Annotated[list[GroupKey], Json()]) -> None:
        """Delete several groups at once.

        Their rules, lists and clients stay, but no longer belong to them.
        Don't delete the Default group, ID `0`: Pi-hole re-creates it, but
        empty, so every rule, list and client in it stops applying until it's
        added back. Groups that don't exist are skipped, but if none of them
        exists, it answers with an error (404).

        Args:
            groups: The groups to delete, each by its name.
        """
        ...


class AsyncGroups(AsyncResource, prefix="/groups"):
    """The Pi-hole's groups of clients, which rules and lists apply to."""

    batch = AsyncGroupsBatch()

    @method.get("/{name}")
    async def get(self, name: str) -> GroupsResponse:
        """Fetch one group by its name.

        It returns the group in a list, or an empty list if there's no such
        group. It changes nothing.

        Args:
            name: The group's name, such as `Kids`.
        """
        ...

    @method.post()
    async def add(
        self,
        name: Annotated[str | list[str], Json()],
        comment: Annotated[str | None, Json()] = None,
        enabled: Annotated[bool, Json()] = True,
    ) -> ChangedGroupsResponse:
        """Add one or more groups.

        A new group has no clients, rules or lists: give it some through
        their `groups`. Each name is saved or refused on its own, such as one
        already taken, and `processed` says which; if all are refused, it
        answers with an error.

        Args:
            name: The group's name, or a list of names, such as `Kids`.
            comment: A note on the group, such as `Bedtime filtering`.
            enabled: `false` to add the group without putting it in effect.
        """
        ...

    @method.put("/{name}")
    async def update(
        self,
        name: str,
        comment: Annotated[str | None, Json()] = None,
        enabled: Annotated[bool, Json()] = True,
    ) -> ChangedGroupsResponse:
        """Change a group's comment or state.

        It replaces the group's settings: a comment left out is removed, and
        `enabled` left out means enabled. If there's no such group, it adds
        one. To rename a group, use the rename endpoint. It takes effect
        right away.

        Args:
            name: The group's name, such as `Kids`.
            comment: The group's comment, such as `Bedtime filtering`. Leave
                it out to remove the current one.
            enabled: `false` to keep the group but take it out of effect.
        """
        ...

    # Pi-hole renames a group with a PUT whose body has the new name.
    @method.put("/{name}")
    async def rename(
        self,
        name: str,
        new_name: Annotated[str, Json(alias="name")],
        comment: Annotated[str | None, Json()] = None,
        enabled: Annotated[bool, Json()] = True,
    ) -> ChangedGroupsResponse:
        """Rename a group.

        Its ID, clients, rules and lists stay. It also replaces the group's
        settings, as an update does: a comment left out is removed, and
        `enabled` left out means enabled. It takes effect right away.

        Args:
            name: The group's name now, such as `Kids`.
            new_name: The name to give it, such as `Children`.
            comment: The group's comment, such as `Bedtime filtering`. Leave
                it out to remove the current one.
            enabled: `false` to keep the group but take it out of effect.
        """
        ...

    @method.delete("/{name}")
    async def delete(self, name: str) -> None:
        """Delete a group.

        Its rules, lists and clients stay, but no longer belong to it. Don't
        delete the Default group, ID `0`: Pi-hole re-creates it, but empty, so
        every rule, list and client in it stops applying until it's added
        back. A group that doesn't exist answers with an error (404).

        Args:
            name: The group's name, such as `Kids`.
        """
        ...

    # Last in the class: a method named `list` hides the builtin for the rest
    # of the class body.
    @method.get()
    async def list(self) -> GroupsResponse:
        """Fetch the Pi-hole's groups of clients.

        Rules, lists and clients belong to groups by ID, and a rule or list
        applies to the clients in its groups. `Default`, ID `0`, holds every
        client the Pi-hole doesn't know, and gets every new rule, list and
        client. It changes nothing.
        """
        ...
