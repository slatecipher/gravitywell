"""The DNS control endpoints, under `/dns`."""

from typing import Annotated

from clientx import AsyncResource, Json, Resource, method
from clientx.tools import ToolOptions

from gravitywell.models import BlockingResponse

# A POST, so AI tools would treat it as neither: it overwrites the blocking
# status, and setting the same status again changes nothing more.
_SET_BLOCKING = ToolOptions(destructive=True, idempotent=True)


class Dns(Resource, prefix="/dns"):
    """Control the Pi-hole's blocking."""

    @method.get("/blocking")
    def blocking(self) -> BlockingResponse:
        """Fetch whether the Pi-hole is blocking ads and trackers right now.

        Use it to check the status before turning blocking on or off, or to
        see how long a temporary change has left: `timer` counts the seconds
        until the status switches back. It changes nothing.
        """
        ...

    @method.post("/blocking", tool_options=_SET_BLOCKING)
    def set_blocking(
        self,
        blocking: Annotated[bool, Json()],
        timer: Annotated[float | None, Json(gt=0)] = None,
    ) -> BlockingResponse:
        """Turn the Pi-hole's blocking of ads and trackers on or off.

        The change applies right away to every device that uses the Pi-hole
        for DNS. With `timer`, the Pi-hole switches back on its own after that
        many seconds, such as `blocking=false, timer=300` to pause blocking
        for five minutes; without it, the change is permanent and cancels any
        running timer. Returns the new status. A Pi-hole whose DNS server
        isn't running answers with an error instead.

        Args:
            blocking: `true` to block ads and trackers, `false` to let every
                domain through.
            timer: Seconds until the Pi-hole switches back to the opposite
                status, more than 0, such as `300` for five minutes. Leave it
                out for a permanent change.
        """
        ...


class AsyncDns(AsyncResource, prefix="/dns"):
    """Control the Pi-hole's blocking."""

    @method.get("/blocking")
    async def blocking(self) -> BlockingResponse:
        """Fetch whether the Pi-hole is blocking ads and trackers right now.

        Use it to check the status before turning blocking on or off, or to
        see how long a temporary change has left: `timer` counts the seconds
        until the status switches back. It changes nothing.
        """
        ...

    @method.post("/blocking", tool_options=_SET_BLOCKING)
    async def set_blocking(
        self,
        blocking: Annotated[bool, Json()],
        timer: Annotated[float | None, Json(gt=0)] = None,
    ) -> BlockingResponse:
        """Turn the Pi-hole's blocking of ads and trackers on or off.

        The change applies right away to every device that uses the Pi-hole
        for DNS. With `timer`, the Pi-hole switches back on its own after that
        many seconds, such as `blocking=false, timer=300` to pause blocking
        for five minutes; without it, the change is permanent and cancels any
        running timer. Returns the new status. A Pi-hole whose DNS server
        isn't running answers with an error instead.

        Args:
            blocking: `true` to block ads and trackers, `false` to let every
                domain through.
            timer: Seconds until the Pi-hole switches back to the opposite
                status, more than 0, such as `300` for five minutes. Leave it
                out for a permanent change.
        """
        ...
