"""Models for the client management endpoints, under `/clients`."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from gravitywell.models._base import GROUP_IDS, BaseResponse, ProcessedItems, zero_as_none


def _comma_list(value: object) -> object:
    # Pi-hole sends a device's addresses and names as one comma-separated
    # string, or `null` for none. A list, such as from a dump, is kept.
    if value is None:
        return []
    if isinstance(value, str):
        return [item for item in value.split(",") if item]
    return value


class ConfiguredClient(BaseModel):
    """A client the Pi-hole recognizes by an identifier, with its groups."""

    client: str = Field(
        description="How the Pi-hole recognizes it: an IP address such as `192.168.1.235`, a subnet such as "
        "`192.168.2.0/24`, a MAC address such as `12:34:56:78:9A:BC`, a hostname such as `laptop.lan`, or an "
        "interface such as `:eth0`. Fetching and deleting it take it exactly as shown, case included."
    )
    name: str = Field(description="The hostname its IP or MAC address resolves to, or an empty string if none.")
    comment: str | None = Field(description="The client's comment, if any.")
    groups: list[int] = Field(description=GROUP_IDS.replace("it applies to", "it's in"))
    id: int = Field(description="The client's ID in the Pi-hole's database.")
    date_added: datetime = Field(description="When the client was added, in UTC.")
    date_modified: datetime = Field(description="When the client last changed, in UTC.")


class ClientKey(BaseModel):
    """Which client to delete."""

    client: str = Field(serialization_alias="item", description="The client's identifier, exactly as `list` shows it.")


class ClientSuggestion(BaseModel):
    """A device the Pi-hole has seen that isn't a configured client yet."""

    # Pi-hole's names, or the field names a dump or an AI tool's result uses.
    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)

    hwaddr: str = Field(
        description="Its MAC address, such as `0e:18:ee:8b:97:9b`, or `ip-` and its IP address when the Pi-hole "
        "doesn't know its MAC address, such as `ip-192.168.1.235`."
    )
    mac_vendor: str = Field(
        alias="macVendor", description="The maker its MAC address belongs to, or an empty string if unknown."
    )
    last_query: Annotated[datetime | None, BeforeValidator(zero_as_none)] = Field(
        alias="lastQuery", description="When it last sent a query, in UTC, or `null` if never."
    )
    addresses: Annotated[list[str], BeforeValidator(_comma_list)] = Field(
        description="Its IP addresses, such as `192.168.1.235`, each usable as a client identifier."
    )
    names: Annotated[list[str], BeforeValidator(_comma_list)] = Field(description="Its hostnames, if known.")


class ClientsResponse(BaseResponse):
    """The clients the Pi-hole recognizes, with their groups."""

    clients: list[ConfiguredClient] = Field(description="The clients.")


class ChangedClientsResponse(BaseResponse):
    """A client after a change, and which clients the change saved."""

    clients: list[ConfiguredClient] = Field(
        description="The client as it is now. When several clients were added, the last of them."
    )
    processed: ProcessedItems | None = Field(description="Which clients were saved, and which weren't and why.")


class ClientSuggestionsResponse(BaseResponse):
    """Devices the Pi-hole has seen that aren't configured clients yet."""

    clients: list[ClientSuggestion] = Field(description="Up to `count` devices, the most recently active first.")
