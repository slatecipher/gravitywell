"""The client management endpoints, under `/clients`."""

from typing import Annotated

from clientx import AsyncResource, Json, Query, Resource, method
from clientx.tools import ToolOptions

from gravitywell.models import ChangedClientsResponse, ClientKey, ClientsResponse, ClientSuggestionsResponse

# A POST, so AI tools would treat it as neither: it deletes, and deleting the
# same clients again changes nothing more.
_BATCH_DELETE = ToolOptions(destructive=True, idempotent=True)


class ClientsBatch(Resource, tags=["clients"]):
    """Change several clients at once."""

    # The full path: ClientX joins a prefix and `:batchDelete` with a slash
    # (ClientX #173).
    @method.post("/clients:batchDelete", tool_options=_BATCH_DELETE)
    def delete(self, clients: Annotated[list[ClientKey], Json()]) -> None:
        """Delete several clients at once.

        Their devices fall back to the Default group. It takes effect right
        away. Clients that don't exist are skipped, but if none of them
        exists, it answers with an error (404).

        Args:
            clients: The clients to delete, each by its identifier.
        """
        ...


class Clients(Resource, prefix="/clients", tags=["clients"]):
    """The clients the Pi-hole recognizes, and the groups they're in."""

    batch = ClientsBatch()

    @method.get("/_suggestions")
    def suggestions(self, count: Annotated[int, Query(ge=1)] = 50) -> ClientSuggestionsResponse:
        """Fetch devices the Pi-hole has seen that aren't configured clients.

        Each comes with its MAC address, maker, IP addresses and hostnames,
        the most recently active first. Use it to find the identifier to add
        a device as a client with. It changes nothing.

        Args:
            count: How many devices to return, at least 1. 50 by default.
        """
        ...

    @method.get("/{client}")
    def get(self, client: str) -> ClientsResponse:
        """Fetch one client by its identifier.

        It returns the client in a list, or an empty list if there's no such
        client. It changes nothing.

        Args:
            client: The client's identifier, exactly as `list` shows it, such
                as `192.168.1.235`.
        """
        ...

    @method.post()
    def add(
        self,
        client: Annotated[str | list[str], Json()],
        comment: Annotated[str | None, Json()] = None,
        groups: Annotated[list[int] | None, Json()] = None,
    ) -> ChangedClientsResponse:
        """Add one or more clients, to put devices into groups.

        A client's queries get the rules and lists of its groups; a device
        that isn't a client is in the Default group. Recognizing by IP address
        or subnet works right away and is preferred: a MAC address or hostname
        is recognized only after the Pi-hole has seen the device, and a MAC
        address only for a device at most one network hop away. Each client is
        saved or refused on its own, such as one that already exists, and
        `processed` says which; if all are refused, it answers with an error.

        Args:
            client: The identifier, or a list of them: an IP address such as
                `192.168.1.235`, a subnet such as `192.168.2.0/24`, a MAC
                address such as `12:34:56:78:9A:BC`, a hostname such as
                `laptop.lan`, or an interface such as `:eth0`.
            comment: A note on the client, such as `Living room TV`.
            groups: IDs of the groups to put it in. Leave it out for the
                Default group, `0`.
        """
        ...

    @method.put("/{client}")
    def update(
        self,
        client: str,
        comment: Annotated[str | None, Json()] = None,
        groups: Annotated[list[int] | None, Json()] = None,
    ) -> ChangedClientsResponse:
        """Change a client's comment or groups.

        It replaces the client's comment: one left out is removed. Groups left
        out stay as they are. If there's no such client, it adds one. It takes
        effect right away.

        Args:
            client: The client's identifier, exactly as `list` shows it, such
                as `192.168.1.235`.
            comment: The client's comment, such as `Living room TV`. Leave it
                out to remove the current one.
            groups: IDs of the groups to put it in, replacing its current
                ones. Leave it out to keep them.
        """
        ...

    @method.delete("/{client}")
    def delete(self, client: str) -> None:
        """Delete a client.

        Its device falls back to the Default group. It takes effect right
        away. A client that doesn't exist answers with an error (404). To
        delete several clients at once, use the batch delete.

        Args:
            client: The client's identifier, exactly as `list` shows it, such
                as `192.168.1.235`.
        """
        ...

    # Last in the class: a method named `list` hides the builtin for the rest
    # of the class body.
    @method.get()
    def list(self) -> ClientsResponse:
        """Fetch the clients the Pi-hole recognizes, with their groups.

        A client is a device, or a range of them, that the Pi-hole recognizes
        by an IP address, subnet, MAC address, hostname or interface, so its
        queries get the rules and lists of its groups. Devices that aren't
        clients are in the Default group. It changes nothing.
        """
        ...


class AsyncClientsBatch(AsyncResource, tags=["clients"]):
    """Change several clients at once."""

    # The full path: ClientX joins a prefix and `:batchDelete` with a slash
    # (ClientX #173).
    @method.post("/clients:batchDelete", tool_options=_BATCH_DELETE)
    async def delete(self, clients: Annotated[list[ClientKey], Json()]) -> None:
        """Delete several clients at once.

        Their devices fall back to the Default group. It takes effect right
        away. Clients that don't exist are skipped, but if none of them
        exists, it answers with an error (404).

        Args:
            clients: The clients to delete, each by its identifier.
        """
        ...


class AsyncClients(AsyncResource, prefix="/clients", tags=["clients"]):
    """The clients the Pi-hole recognizes, and the groups they're in."""

    batch = AsyncClientsBatch()

    @method.get("/_suggestions")
    async def suggestions(self, count: Annotated[int, Query(ge=1)] = 50) -> ClientSuggestionsResponse:
        """Fetch devices the Pi-hole has seen that aren't configured clients.

        Each comes with its MAC address, maker, IP addresses and hostnames,
        the most recently active first. Use it to find the identifier to add
        a device as a client with. It changes nothing.

        Args:
            count: How many devices to return, at least 1. 50 by default.
        """
        ...

    @method.get("/{client}")
    async def get(self, client: str) -> ClientsResponse:
        """Fetch one client by its identifier.

        It returns the client in a list, or an empty list if there's no such
        client. It changes nothing.

        Args:
            client: The client's identifier, exactly as `list` shows it, such
                as `192.168.1.235`.
        """
        ...

    @method.post()
    async def add(
        self,
        client: Annotated[str | list[str], Json()],
        comment: Annotated[str | None, Json()] = None,
        groups: Annotated[list[int] | None, Json()] = None,
    ) -> ChangedClientsResponse:
        """Add one or more clients, to put devices into groups.

        A client's queries get the rules and lists of its groups; a device
        that isn't a client is in the Default group. Recognizing by IP address
        or subnet works right away and is preferred: a MAC address or hostname
        is recognized only after the Pi-hole has seen the device, and a MAC
        address only for a device at most one network hop away. Each client is
        saved or refused on its own, such as one that already exists, and
        `processed` says which; if all are refused, it answers with an error.

        Args:
            client: The identifier, or a list of them: an IP address such as
                `192.168.1.235`, a subnet such as `192.168.2.0/24`, a MAC
                address such as `12:34:56:78:9A:BC`, a hostname such as
                `laptop.lan`, or an interface such as `:eth0`.
            comment: A note on the client, such as `Living room TV`.
            groups: IDs of the groups to put it in. Leave it out for the
                Default group, `0`.
        """
        ...

    @method.put("/{client}")
    async def update(
        self,
        client: str,
        comment: Annotated[str | None, Json()] = None,
        groups: Annotated[list[int] | None, Json()] = None,
    ) -> ChangedClientsResponse:
        """Change a client's comment or groups.

        It replaces the client's comment: one left out is removed. Groups left
        out stay as they are. If there's no such client, it adds one. It takes
        effect right away.

        Args:
            client: The client's identifier, exactly as `list` shows it, such
                as `192.168.1.235`.
            comment: The client's comment, such as `Living room TV`. Leave it
                out to remove the current one.
            groups: IDs of the groups to put it in, replacing its current
                ones. Leave it out to keep them.
        """
        ...

    @method.delete("/{client}")
    async def delete(self, client: str) -> None:
        """Delete a client.

        Its device falls back to the Default group. It takes effect right
        away. A client that doesn't exist answers with an error (404). To
        delete several clients at once, use the batch delete.

        Args:
            client: The client's identifier, exactly as `list` shows it, such
                as `192.168.1.235`.
        """
        ...

    # Last in the class: a method named `list` hides the builtin for the rest
    # of the class body.
    @method.get()
    async def list(self) -> ClientsResponse:
        """Fetch the clients the Pi-hole recognizes, with their groups.

        A client is a device, or a range of them, that the Pi-hole recognizes
        by an IP address, subnet, MAC address, hostname or interface, so its
        queries get the rules and lists of its groups. Devices that aren't
        clients are in the Default group. It changes nothing.
        """
        ...
