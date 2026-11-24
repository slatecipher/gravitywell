"""The network endpoints, under `/network`."""

from typing import Annotated

from clientx import AsyncResource, Query, Resource, method

from gravitywell.models import GatewayResponse, InterfacesResponse, NetworkDevicesResponse, RoutesResponse


class Network(Resource, prefix="/network", tags=["network"]):
    """The network the Pi-hole sees: devices, interfaces, routes and gateway."""

    @method.get("/devices")
    def devices(
        self,
        max_devices: Annotated[int, Query(ge=1)] = 10,
        max_addresses: Annotated[int, Query(ge=1)] = 3,
    ) -> NetworkDevicesResponse:
        """Fetch the devices the Pi-hole has seen on the network.

        Each comes with its MAC address, maker, IP addresses and hostnames,
        and how many queries it sent and when, the most recently active first.
        Use it to tell which device an IP address belongs to, or which devices
        use the Pi-hole. It changes nothing.

        Args:
            max_devices: How many devices to return, at least 1. 10 by
                default.
            max_addresses: How many IP addresses to return for each device, at
                least 1. 3 by default.
        """
        ...

    @method.delete("/devices/{device_id}")
    def delete_device(self, device_id: int) -> None:
        """Remove a device from the Pi-hole's network table.

        It only forgets what the Pi-hole knew about the device: a device that
        sends another query is added again. A device that doesn't exist
        answers with an error (404).

        Args:
            device_id: The device's ID, as `devices` shows it.
        """
        ...

    @method.get("/gateway")
    def gateway(self) -> GatewayResponse:
        """Fetch the Pi-hole machine's default routes and gateways.

        Use it to find the router the Pi-hole reaches the internet through,
        and its own addresses on that network. It changes nothing.
        """
        ...

    @method.get("/interfaces")
    def interfaces(self) -> InterfacesResponse:
        """Fetch the Pi-hole machine's network interfaces.

        Each comes with its state, link, speed, IP addresses and traffic. Use
        it to check that the interface the Pi-hole serves DNS on is up and has
        the expected address. It changes nothing.
        """
        ...

    @method.get("/routes")
    def routes(self) -> RoutesResponse:
        """Fetch the Pi-hole machine's routes, from every routing table.

        For the default route alone, the gateway endpoint is simpler. It
        changes nothing.
        """
        ...


class AsyncNetwork(AsyncResource, prefix="/network", tags=["network"]):
    """The network the Pi-hole sees: devices, interfaces, routes and gateway."""

    @method.get("/devices")
    async def devices(
        self,
        max_devices: Annotated[int, Query(ge=1)] = 10,
        max_addresses: Annotated[int, Query(ge=1)] = 3,
    ) -> NetworkDevicesResponse:
        """Fetch the devices the Pi-hole has seen on the network.

        Each comes with its MAC address, maker, IP addresses and hostnames,
        and how many queries it sent and when, the most recently active first.
        Use it to tell which device an IP address belongs to, or which devices
        use the Pi-hole. It changes nothing.

        Args:
            max_devices: How many devices to return, at least 1. 10 by
                default.
            max_addresses: How many IP addresses to return for each device, at
                least 1. 3 by default.
        """
        ...

    @method.delete("/devices/{device_id}")
    async def delete_device(self, device_id: int) -> None:
        """Remove a device from the Pi-hole's network table.

        It only forgets what the Pi-hole knew about the device: a device that
        sends another query is added again. A device that doesn't exist
        answers with an error (404).

        Args:
            device_id: The device's ID, as `devices` shows it.
        """
        ...

    @method.get("/gateway")
    async def gateway(self) -> GatewayResponse:
        """Fetch the Pi-hole machine's default routes and gateways.

        Use it to find the router the Pi-hole reaches the internet through,
        and its own addresses on that network. It changes nothing.
        """
        ...

    @method.get("/interfaces")
    async def interfaces(self) -> InterfacesResponse:
        """Fetch the Pi-hole machine's network interfaces.

        Each comes with its state, link, speed, IP addresses and traffic. Use
        it to check that the interface the Pi-hole serves DNS on is up and has
        the expected address. It changes nothing.
        """
        ...

    @method.get("/routes")
    async def routes(self) -> RoutesResponse:
        """Fetch the Pi-hole machine's routes, from every routing table.

        For the default route alone, the gateway endpoint is simpler. It
        changes nothing.
        """
        ...
