"""Models for the configuration endpoints, under `/config`."""

from pydantic import BaseModel, Field

from gravitywell.models._base import BaseResponse


class DnsRecord(BaseModel):
    """A local DNS record: hostnames the Pi-hole answers with an IP address."""

    ip: str = Field(description="The IP address, IPv4 or IPv6, such as `192.168.1.10`.")
    hostnames: list[str] = Field(description="The hostnames it answers for, such as `nas.lan`. Usually one.")


class DnsRecordsResponse(BaseResponse):
    """The Pi-hole's local DNS records."""

    records: list[DnsRecord] = Field(description="The records, the oldest first.")


class CnameRecord(BaseModel):
    """A local CNAME record: aliases the Pi-hole answers with another domain."""

    domains: list[str] = Field(description="The aliases, such as `files.lan`. Usually one.")
    target: str = Field(description="The domain they stand for, such as `nas.lan`.")
    ttl: int | None = Field(
        description="How long clients may cache the answer, in seconds, or `null` for dnsmasq's local TTL, 0 "
        "unless `misc.dnsmasq_lines` sets `local-ttl`."
    )


class CnameRecordsResponse(BaseResponse):
    """The Pi-hole's local CNAME records."""

    records: list[CnameRecord] = Field(description="The records, the oldest first.")


class UpstreamServersResponse(BaseResponse):
    """The DNS servers the Pi-hole forwards the queries it can't answer to."""

    servers: list[str] = Field(
        description="The servers: IP addresses or hostnames, optionally with a port after `#`, such as `9.9.9.9` or "
        "`127.0.0.1#5335`."
    )
