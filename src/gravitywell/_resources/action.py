"""The action endpoints, under `/action`."""

import re

from clientx import AsyncResource, Resource, Response, Timeout, method
from clientx.tools import ToolOptions

from gravitywell.models import GravityUpdate

# A gravity update sends its output as it goes, but can go quiet for minutes
# on large lists, so allow up to 10 minutes between chunks.
_GRAVITY_TIMEOUT = Timeout(10.0, read=600.0)
# A terminal control sequence, such as `\x1b[K`, which clears the line, or a
# NUL byte.
_CONTROL = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\x00")


def _gravity_update(response: Response) -> GravityUpdate:
    """Read `pihole -g`'s output as the lines a terminal would show.

    It replaces each step's progress line with its result, by a carriage
    return and a code that clears the line, so only the text after a line's
    last carriage return stays. FTL ends the output with `Gravity failed` if
    the update failed, as it has already answered 200.
    """
    lines = [_CONTROL.sub("", line).rsplit("\r", 1)[-1] for line in response.text.split("\n")]
    output = "\n".join(lines).strip("\n")
    return GravityUpdate(output=output, succeeded=output.rsplit("\n", 1)[-1] != "Gravity failed")


class Action(Resource, prefix="/action"):
    """Actions on the Pi-hole: update gravity, restart FTL, and flush data."""

    @method.post(
        "/gravity",
        decoder=_gravity_update,
        timeout=_GRAVITY_TIMEOUT,
        tool_options=ToolOptions(destructive=True, idempotent=True),
    )
    def update_gravity(self) -> GravityUpdate:
        """Update gravity, downloading the lists and rebuilding their domains.

        Run it after adding a list or changing its URL: a list's domains take
        effect only once an update downloads them. It takes seconds to
        minutes, depending on the lists, and returns each list's download
        status and domain count. It replaces the domains of the last update,
        so a domain a list dropped stops being blocked, though rules, groups
        and clients stay as they are. Only one update runs at a time: another
        answers with an error (409). A failed update still returns, with
        `succeeded` false.
        """
        ...

    @method.post("/restartdns", tool_options=ToolOptions(idempotent=True))
    def restart_dns(self) -> None:
        """Restart FTL, the Pi-hole's DNS server, web server and API.

        FTL saves its queries and sessions and starts again: for a few
        seconds, devices that use the Pi-hole can't resolve names and the API
        doesn't answer. Use it when DNS misbehaves, or after a change that
        asks for a restart. It answers with an error (403) if the Pi-hole's
        `webserver.api.allow_destructive` setting is off.
        """
        ...

    @method.post("/flush/logs", tool_options=ToolOptions(destructive=True, idempotent=True))
    def flush_logs(self) -> None:
        """Delete the last 24 hours of queries and the DNS resolver's log.

        It clears every query from FTL's memory, so the statistics, query log
        and recent history start again from zero, deletes the last 24 hours of
        queries from the long-term database, keeping older ones, and empties
        dnsmasq's log. It can't be undone: use it only when asked to clear the
        query history. It answers with an error (403) if the Pi-hole's
        `webserver.api.allow_destructive` setting is off.
        """
        ...

    @method.post("/flush/network", tool_options=ToolOptions(destructive=True, idempotent=True))
    def flush_network(self) -> None:
        """Forget every device in the Pi-hole's network table.

        It deletes all devices, with their addresses and hostnames. A device
        is added again when it sends a query, but its first-seen time and
        query count start over. To forget one device, deleting it alone is
        better. It answers with an error (403) if the Pi-hole's
        `webserver.api.allow_destructive` setting is off.
        """
        ...


class AsyncAction(AsyncResource, prefix="/action"):
    """Actions on the Pi-hole: update gravity, restart FTL, and flush data."""

    @method.post(
        "/gravity",
        decoder=_gravity_update,
        timeout=_GRAVITY_TIMEOUT,
        tool_options=ToolOptions(destructive=True, idempotent=True),
    )
    async def update_gravity(self) -> GravityUpdate:
        """Update gravity, downloading the lists and rebuilding their domains.

        Run it after adding a list or changing its URL: a list's domains take
        effect only once an update downloads them. It takes seconds to
        minutes, depending on the lists, and returns each list's download
        status and domain count. It replaces the domains of the last update,
        so a domain a list dropped stops being blocked, though rules, groups
        and clients stay as they are. Only one update runs at a time: another
        answers with an error (409). A failed update still returns, with
        `succeeded` false.
        """
        ...

    @method.post("/restartdns", tool_options=ToolOptions(idempotent=True))
    async def restart_dns(self) -> None:
        """Restart FTL, the Pi-hole's DNS server, web server and API.

        FTL saves its queries and sessions and starts again: for a few
        seconds, devices that use the Pi-hole can't resolve names and the API
        doesn't answer. Use it when DNS misbehaves, or after a change that
        asks for a restart. It answers with an error (403) if the Pi-hole's
        `webserver.api.allow_destructive` setting is off.
        """
        ...

    @method.post("/flush/logs", tool_options=ToolOptions(destructive=True, idempotent=True))
    async def flush_logs(self) -> None:
        """Delete the last 24 hours of queries and the DNS resolver's log.

        It clears every query from FTL's memory, so the statistics, query log
        and recent history start again from zero, deletes the last 24 hours of
        queries from the long-term database, keeping older ones, and empties
        dnsmasq's log. It can't be undone: use it only when asked to clear the
        query history. It answers with an error (403) if the Pi-hole's
        `webserver.api.allow_destructive` setting is off.
        """
        ...

    @method.post("/flush/network", tool_options=ToolOptions(destructive=True, idempotent=True))
    async def flush_network(self) -> None:
        """Forget every device in the Pi-hole's network table.

        It deletes all devices, with their addresses and hostnames. A device
        is added again when it sends a query, but its first-seen time and
        query count start over. To forget one device, deleting it alone is
        better. It answers with an error (403) if the Pi-hole's
        `webserver.api.allow_destructive` setting is off.
        """
        ...
