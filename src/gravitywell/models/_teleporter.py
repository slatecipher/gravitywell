"""Models for Teleporter backups, under `/teleporter`."""

from pydantic import BaseModel, Field

from gravitywell.models._base import BaseResponse


class GravityTables(BaseModel):
    """Which of the gravity database's tables to restore."""

    group: bool = Field(default=True, description="The groups.")
    adlist: bool = Field(default=True, description="The lists.")
    adlist_by_group: bool = Field(default=True, description="Which groups each list applies to.")
    domainlist: bool = Field(default=True, description="The domain rules.")
    domainlist_by_group: bool = Field(default=True, description="Which groups each domain rule applies to.")
    client: bool = Field(default=True, description="The clients.")
    client_by_group: bool = Field(default=True, description="Which groups each client is in.")


class RestoreParts(BaseModel):
    """What to restore from a Teleporter archive: everything by default."""

    config: bool = Field(default=True, description="The settings, `pihole.toml`, with local DNS records and passwords.")
    dhcp_leases: bool = Field(default=True, description="The DHCP leases.")
    gravity: GravityTables = Field(default_factory=GravityTables, description="The gravity database's tables.")


class RestoreResponse(BaseResponse):
    """What a Teleporter restore restored."""

    files: list[str] = Field(
        description="The files and gravity tables restored, such as `etc/pihole/pihole.toml` and "
        "`etc/pihole/gravity.db->group`."
    )
