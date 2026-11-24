"""The list management endpoints, under `/lists`."""

from typing import Annotated

from clientx import AsyncResource, Json, Query, Resource, method
from clientx.tools import ToolOptions

from gravitywell.models import ChangedListsResponse, ListKey, ListsResponse, ListType

# A POST, so AI tools would treat it as neither: it deletes, and deleting the
# same lists again changes nothing more.
_BATCH_DELETE = ToolOptions(destructive=True, idempotent=True)


class ListsBatch(Resource):
    """Change several subscribed lists at once."""

    # The full path: ClientX joins a prefix and `:batchDelete` with a slash
    # (ClientX #173).
    @method.post("/lists:batchDelete", tool_options=_BATCH_DELETE)
    def delete(self, lists: Annotated[list[ListKey], Json()]) -> None:
        """Unsubscribe the Pi-hole from several lists at once.

        It takes effect right away. Lists it doesn't subscribe to are skipped,
        but if it subscribes to none of them, it answers with an error (404).

        Args:
            lists: The lists to unsubscribe from, each by its URL and type.
        """
        ...


class Lists(Resource, prefix="/lists"):
    """The blocklists and allowlists the Pi-hole subscribes to."""

    batch = ListsBatch()

    @method.get("/{address}")
    def get(self, address: str, list_type: Annotated[ListType | None, Query(alias="type")] = None) -> ListsResponse:
        """Fetch one subscribed list by its URL.

        It returns the list in a list, or an empty list if the Pi-hole doesn't
        subscribe to it. It changes nothing.

        Args:
            address: The list's URL, such as
                `https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts`.
            list_type: `block` or `allow`, for a URL subscribed as both. Leave
                it out for either.
        """
        ...

    @method.post()
    def add(
        self,
        list_type: Annotated[ListType, Query(alias="type")],
        address: Annotated[str | list[str], Json()],
        comment: Annotated[str | None, Json()] = None,
        groups: Annotated[list[int] | None, Json()] = None,
        enabled: Annotated[bool, Json()] = True,
    ) -> ChangedListsResponse:
        """Subscribe the Pi-hole to one or more blocklists or allowlists.

        A new list's domains take effect only after a gravity update, from
        the update gravity endpoint, downloads it. Each URL is saved or
        refused on its own, such as one it already subscribes to, and
        `processed` says which; if all are refused, it answers with an error.

        Args:
            list_type: `block` for blocklists, whose domains are blocked, or
                `allow` for allowlists, whose domains are let through even
                when a blocklist has them.
            address: The list's URL, or a list of URLs, such as
                `https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts`.
            comment: A note on the list, such as `Ads and trackers`.
            groups: IDs of the groups the list applies to. Leave it out for
                the Default group, `0`.
            enabled: `false` to subscribe without putting the list in effect.
        """
        ...

    @method.put("/{address}")
    def update(
        self,
        address: str,
        list_type: Annotated[ListType, Query(alias="type")],
        comment: Annotated[str | None, Json()] = None,
        groups: Annotated[list[int] | None, Json()] = None,
        enabled: Annotated[bool, Json()] = True,
    ) -> ChangedListsResponse:
        """Change a subscribed list's comment, groups or state.

        It replaces the list's settings: a comment left out is removed, and
        `enabled` left out means enabled, while groups left out stay as they
        are. If the Pi-hole doesn't subscribe to the list, it subscribes. A
        list's type can't change: delete it and add it with the other type.
        It takes effect right away, though a list never downloaded needs a
        gravity update first, from the update gravity endpoint.

        Args:
            address: The list's URL, such as
                `https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts`.
            list_type: The list's type: `block` or `allow`.
            comment: The list's comment, such as `Ads and trackers`. Leave it
                out to remove the current one.
            groups: IDs of the groups the list applies to. Leave it out to
                keep the current ones.
            enabled: `false` to keep the list but take it out of effect.
        """
        ...

    @method.delete("/{address}")
    def delete(self, address: str, list_type: Annotated[ListType, Query(alias="type")]) -> None:
        """Unsubscribe the Pi-hole from a list.

        It takes effect right away. A list it doesn't subscribe to answers
        with an error (404). To unsubscribe from several lists at once, use
        the batch delete.

        Args:
            address: The list's URL, such as
                `https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts`.
            list_type: The list's type: `block` or `allow`.
        """
        ...

    # Last in the class: a method named `list` hides the builtin for the rest
    # of the class body.
    @method.get()
    def list(self, list_type: Annotated[ListType | None, Query(alias="type")] = None) -> ListsResponse:
        """Fetch the blocklists and allowlists the Pi-hole subscribes to.

        Each is a URL the Pi-hole downloads domains from in a gravity update,
        with how many domains it had and how its last download went
        (`status`). It changes nothing.

        Args:
            list_type: `block` or `allow` for only that type. Leave it out for
                both.
        """
        ...


class AsyncListsBatch(AsyncResource):
    """Change several subscribed lists at once."""

    # The full path: ClientX joins a prefix and `:batchDelete` with a slash
    # (ClientX #173).
    @method.post("/lists:batchDelete", tool_options=_BATCH_DELETE)
    async def delete(self, lists: Annotated[list[ListKey], Json()]) -> None:
        """Unsubscribe the Pi-hole from several lists at once.

        It takes effect right away. Lists it doesn't subscribe to are skipped,
        but if it subscribes to none of them, it answers with an error (404).

        Args:
            lists: The lists to unsubscribe from, each by its URL and type.
        """
        ...


class AsyncLists(AsyncResource, prefix="/lists"):
    """The blocklists and allowlists the Pi-hole subscribes to."""

    batch = AsyncListsBatch()

    @method.get("/{address}")
    async def get(
        self, address: str, list_type: Annotated[ListType | None, Query(alias="type")] = None
    ) -> ListsResponse:
        """Fetch one subscribed list by its URL.

        It returns the list in a list, or an empty list if the Pi-hole doesn't
        subscribe to it. It changes nothing.

        Args:
            address: The list's URL, such as
                `https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts`.
            list_type: `block` or `allow`, for a URL subscribed as both. Leave
                it out for either.
        """
        ...

    @method.post()
    async def add(
        self,
        list_type: Annotated[ListType, Query(alias="type")],
        address: Annotated[str | list[str], Json()],
        comment: Annotated[str | None, Json()] = None,
        groups: Annotated[list[int] | None, Json()] = None,
        enabled: Annotated[bool, Json()] = True,
    ) -> ChangedListsResponse:
        """Subscribe the Pi-hole to one or more blocklists or allowlists.

        A new list's domains take effect only after a gravity update, from
        the update gravity endpoint, downloads it. Each URL is saved or
        refused on its own, such as one it already subscribes to, and
        `processed` says which; if all are refused, it answers with an error.

        Args:
            list_type: `block` for blocklists, whose domains are blocked, or
                `allow` for allowlists, whose domains are let through even
                when a blocklist has them.
            address: The list's URL, or a list of URLs, such as
                `https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts`.
            comment: A note on the list, such as `Ads and trackers`.
            groups: IDs of the groups the list applies to. Leave it out for
                the Default group, `0`.
            enabled: `false` to subscribe without putting the list in effect.
        """
        ...

    @method.put("/{address}")
    async def update(
        self,
        address: str,
        list_type: Annotated[ListType, Query(alias="type")],
        comment: Annotated[str | None, Json()] = None,
        groups: Annotated[list[int] | None, Json()] = None,
        enabled: Annotated[bool, Json()] = True,
    ) -> ChangedListsResponse:
        """Change a subscribed list's comment, groups or state.

        It replaces the list's settings: a comment left out is removed, and
        `enabled` left out means enabled, while groups left out stay as they
        are. If the Pi-hole doesn't subscribe to the list, it subscribes. A
        list's type can't change: delete it and add it with the other type.
        It takes effect right away, though a list never downloaded needs a
        gravity update first, from the update gravity endpoint.

        Args:
            address: The list's URL, such as
                `https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts`.
            list_type: The list's type: `block` or `allow`.
            comment: The list's comment, such as `Ads and trackers`. Leave it
                out to remove the current one.
            groups: IDs of the groups the list applies to. Leave it out to
                keep the current ones.
            enabled: `false` to keep the list but take it out of effect.
        """
        ...

    @method.delete("/{address}")
    async def delete(self, address: str, list_type: Annotated[ListType, Query(alias="type")]) -> None:
        """Unsubscribe the Pi-hole from a list.

        It takes effect right away. A list it doesn't subscribe to answers
        with an error (404). To unsubscribe from several lists at once, use
        the batch delete.

        Args:
            address: The list's URL, such as
                `https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts`.
            list_type: The list's type: `block` or `allow`.
        """
        ...

    # Last in the class: a method named `list` hides the builtin for the rest
    # of the class body.
    @method.get()
    async def list(self, list_type: Annotated[ListType | None, Query(alias="type")] = None) -> ListsResponse:
        """Fetch the blocklists and allowlists the Pi-hole subscribes to.

        Each is a URL the Pi-hole downloads domains from in a gravity update,
        with how many domains it had and how its last download went
        (`status`). It changes nothing.

        Args:
            list_type: `block` or `allow` for only that type. Leave it out for
                both.
        """
        ...
