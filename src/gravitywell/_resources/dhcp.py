"""The DHCP endpoints, under `/dhcp`."""

from clientx import AsyncResource, Resource, method

from gravitywell.models import DhcpLeasesResponse


class Dhcp(Resource, prefix="/dhcp", tags=["dhcp"]):
    """The Pi-hole's DHCP server and its leases."""

    @method.get("/leases")
    def leases(self) -> DhcpLeasesResponse:
        """Fetch the IP addresses the Pi-hole's DHCP server has leased.

        Each lease gives a device's IP address, MAC address, hostname and when
        the lease ends. It's empty unless the Pi-hole serves DHCP. It changes
        nothing.
        """
        ...

    @method.delete("/leases/{ip}")
    def delete_lease(self, ip: str) -> None:
        """End a DHCP lease, freeing its IP address.

        The device keeps using the address until it renews its lease, when it
        may get another one. It answers with an error if the Pi-hole doesn't
        serve DHCP or the address isn't an IP address (400), or if the address
        has no lease (404).

        Args:
            ip: The leased IP address, such as `192.168.1.50`.
        """
        ...


class AsyncDhcp(AsyncResource, prefix="/dhcp", tags=["dhcp"]):
    """The Pi-hole's DHCP server and its leases."""

    @method.get("/leases")
    async def leases(self) -> DhcpLeasesResponse:
        """Fetch the IP addresses the Pi-hole's DHCP server has leased.

        Each lease gives a device's IP address, MAC address, hostname and when
        the lease ends. It's empty unless the Pi-hole serves DHCP. It changes
        nothing.
        """
        ...

    @method.delete("/leases/{ip}")
    async def delete_lease(self, ip: str) -> None:
        """End a DHCP lease, freeing its IP address.

        The device keeps using the address until it renews its lease, when it
        may get another one. It answers with an error if the Pi-hole doesn't
        serve DHCP or the address isn't an IP address (400), or if the address
        has no lease (404).

        Args:
            ip: The leased IP address, such as `192.168.1.50`.
        """
        ...
