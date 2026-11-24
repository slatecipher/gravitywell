"""Models for the history endpoints, under `/history`."""

from datetime import datetime

from pydantic import BaseModel, Field

from gravitywell.models._base import BaseResponse


class ActivitySlot(BaseModel):
    """The Pi-hole's queries in one 10-minute slot."""

    timestamp: datetime = Field(
        description="The middle of the slot, in UTC, such as `2026-11-24T15:25:00Z`. It covers 5 minutes either side."
    )
    total: int = Field(description="Queries in the slot.")
    cached: int = Field(description="Queries answered from the cache.")
    blocked: int = Field(description="Queries blocked.")
    forwarded: int = Field(description="Queries answered by an upstream DNS server.")


class ActivityResponse(BaseResponse):
    """The Pi-hole's queries over the last 24 hours, in 10-minute slots."""

    history: list[ActivitySlot] = Field(
        description="Every slot of the last 24 hours, oldest first, including slots without queries."
    )


class HistoryClient(BaseModel):
    """A client in a per-client history, a device that queries the Pi-hole."""

    name: str | None = Field(
        description="Its hostname, such as `laptop.lan`, or `null` or an empty string if the Pi-hole knows none."
    )
    total: int = Field(description="Its queries in the time the history covers.")


class ClientActivitySlot(BaseModel):
    """Each client's queries in one 10-minute slot."""

    timestamp: datetime = Field(
        description="The middle of the slot, in UTC, such as `2026-11-24T15:25:00Z`. It covers 5 minutes either side."
    )
    data: dict[str, int] = Field(
        description="Queries in the slot per client, keyed by IP address as in `clients`, and `others` for the "
        "clients not listed there."
    )


class ClientActivityResponse(BaseResponse):
    """Each client's queries over the last 24 hours, in 10-minute slots."""

    clients: dict[str, HistoryClient] = Field(
        description="The clients with the most queries, keyed by IP address. With more clients than `count`, the top "
        "`count - 1` are listed and the rest summed under `others`, named `other clients`. Empty if the Pi-hole's "
        "privacy level hides clients."
    )
    history: list[ClientActivitySlot] = Field(description="Every slot of the last 24 hours, oldest first.")


class DatabaseActivitySlot(ActivitySlot):
    """The Pi-hole's queries in one 10-minute slot of its query database."""

    timestamp: datetime = Field(
        description="The start of the slot, in UTC, such as `2026-11-24T15:20:00Z`. It covers the 10 minutes after it."
    )


class DatabaseActivityResponse(BaseResponse):
    """The Pi-hole's queries over a time range, in 10-minute slots."""

    history: list[DatabaseActivitySlot] = Field(
        description="Each slot in the range that has queries, oldest first. Slots without queries are left out."
    )


class DatabaseClientActivitySlot(ClientActivitySlot):
    """Each client's queries in one 10-minute slot of the query database."""

    timestamp: datetime = Field(
        description="The start of the slot, in UTC, such as `2026-11-24T15:20:00Z`. It covers the 10 minutes after it."
    )
    data: dict[str, int] = Field(
        description="Queries in the slot per client, keyed by IP address as in `clients`. Clients without queries in "
        "the slot are left out."
    )


class DatabaseClientActivityResponse(BaseResponse):
    """Each client's queries over a time range, in 10-minute slots."""

    clients: dict[str, HistoryClient] = Field(
        description="Every client that sent a query in the range, keyed by IP address."
    )
    history: list[DatabaseClientActivitySlot] = Field(
        description="Each slot in the range that has queries, newest first. Slots without queries are left out."
    )
