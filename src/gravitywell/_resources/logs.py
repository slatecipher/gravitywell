"""The log endpoints, under `/logs`."""

import re
from typing import Annotated, Literal

from clientx import AsyncResource, Query, Resource, method
from clientx.tools import tool
from pydantic import Field

from gravitywell.models import LogResponse

_LogName = Literal["dnsmasq", "ftl", "webserver"]
# Plain aliases, so AI tools' schemas inline them.
_NextId = Annotated[int | None, Field(ge=0)]
_Lines = Annotated[int | None, Field(ge=1)]

# A session ID in a log line. With the `debug.api` setting on, FTL logs
# `Read sid="..."` for each request, and requests' query strings, where some
# clients send `sid=...`; after a database error, it logs `sid = ...`.
_SESSION_ID = re.compile(r'\b(sid\s*=\s*"?)[^\s"&;]+', re.IGNORECASE)


def _clean(response: LogResponse, lines: int | None) -> LogResponse:
    """Keep the newest `lines` lines, with their session IDs redacted."""
    kept = response.log if lines is None else response.log[max(len(response.log) - lines, 0) :]
    redacted = [line.model_copy(update={"message": _SESSION_ID.sub(r"\1<redacted>", line.message)}) for line in kept]
    return response.model_copy(update={"log": redacted})


class Logs(Resource, prefix="/logs", tags=["logs"]):
    """The logs of the Pi-hole's DNS resolver, FTL and web server."""

    # The raw request for the methods below, which keep the newest lines and
    # redact session IDs. ClientX leaves private names out of AI tools.
    @method.get("/{name}")
    def _log(self, name: _LogName, next_id: Annotated[int | None, Query(alias="nextID")] = None) -> LogResponse: ...

    @tool(read_only=True, idempotent=True)
    def dnsmasq(self, next_id: _NextId = None, lines: _Lines = None) -> LogResponse:
        """Fetch the newest lines of the DNS resolver's log, dnsmasq's.

        It logs each query step by step: who asked, whether it was blocked,
        answered from the cache or forwarded, and the reply, along with DHCP
        and the resolver's own events. Use it to trace how one query was
        answered; to list queries or see which were blocked, the query log is
        easier to read. Pi-hole keeps the last 512 lines. It changes nothing.

        Args:
            next_id: `next_id` from an earlier call, to get only the lines
                written since, for polling: with nothing new, no lines. Leave
                it out to get every line kept, and again when a call returns
                a lower `next_id` than it was given: the log started over.
            lines: How many of the newest lines to return, at least 1. All of
                them by default.
        """
        return _clean(self._log("dnsmasq", next_id), lines)

    @tool(read_only=True, idempotent=True)
    def ftl(self, next_id: _NextId = None, lines: _Lines = None) -> LogResponse:
        """Fetch the newest lines of FTL's log, Pi-hole's own.

        It logs FTL's startup, gravity and database work, and its warnings and
        errors, each with a priority. Use it to find out why something failed;
        the diagnosis messages sum up the problems Pi-hole found. Pi-hole keeps
        the last 512 lines. Session IDs, which FTL logs when its `debug.api`
        setting is on, read as `<redacted>`. It changes nothing.

        Args:
            next_id: `next_id` from an earlier call, to get only the lines
                written since, for polling: with nothing new, no lines. Leave
                it out to get every line kept, and again when a call returns
                a lower `next_id` than it was given: the log started over.
            lines: How many of the newest lines to return, at least 1. All of
                them by default.
        """
        return _clean(self._log("ftl", next_id), lines)

    @tool(read_only=True, idempotent=True)
    def webserver(self, next_id: _NextId = None, lines: _Lines = None) -> LogResponse:
        """Fetch the newest lines of the web server's log.

        It logs the web server's startup, TLS and errors, and each request it
        serves when FTL's `debug.api` setting is on. Use it when the web
        interface or the API doesn't answer as expected. Pi-hole keeps the last
        512 lines. Session IDs in requests read as `<redacted>`. It changes
        nothing.

        Args:
            next_id: `next_id` from an earlier call, to get only the lines
                written since, for polling: with nothing new, no lines. Leave
                it out to get every line kept, and again when a call returns
                a lower `next_id` than it was given: the log started over.
            lines: How many of the newest lines to return, at least 1. All of
                them by default.
        """
        return _clean(self._log("webserver", next_id), lines)


class AsyncLogs(AsyncResource, prefix="/logs", tags=["logs"]):
    """The logs of the Pi-hole's DNS resolver, FTL and web server."""

    # The raw request for the methods below, which keep the newest lines and
    # redact session IDs. ClientX leaves private names out of AI tools.
    @method.get("/{name}")
    async def _log(
        self, name: _LogName, next_id: Annotated[int | None, Query(alias="nextID")] = None
    ) -> LogResponse: ...

    @tool(read_only=True, idempotent=True)
    async def dnsmasq(self, next_id: _NextId = None, lines: _Lines = None) -> LogResponse:
        """Fetch the newest lines of the DNS resolver's log, dnsmasq's.

        It logs each query step by step: who asked, whether it was blocked,
        answered from the cache or forwarded, and the reply, along with DHCP
        and the resolver's own events. Use it to trace how one query was
        answered; to list queries or see which were blocked, the query log is
        easier to read. Pi-hole keeps the last 512 lines. It changes nothing.

        Args:
            next_id: `next_id` from an earlier call, to get only the lines
                written since, for polling: with nothing new, no lines. Leave
                it out to get every line kept, and again when a call returns
                a lower `next_id` than it was given: the log started over.
            lines: How many of the newest lines to return, at least 1. All of
                them by default.
        """
        return _clean(await self._log("dnsmasq", next_id), lines)

    @tool(read_only=True, idempotent=True)
    async def ftl(self, next_id: _NextId = None, lines: _Lines = None) -> LogResponse:
        """Fetch the newest lines of FTL's log, Pi-hole's own.

        It logs FTL's startup, gravity and database work, and its warnings and
        errors, each with a priority. Use it to find out why something failed;
        the diagnosis messages sum up the problems Pi-hole found. Pi-hole keeps
        the last 512 lines. Session IDs, which FTL logs when its `debug.api`
        setting is on, read as `<redacted>`. It changes nothing.

        Args:
            next_id: `next_id` from an earlier call, to get only the lines
                written since, for polling: with nothing new, no lines. Leave
                it out to get every line kept, and again when a call returns
                a lower `next_id` than it was given: the log started over.
            lines: How many of the newest lines to return, at least 1. All of
                them by default.
        """
        return _clean(await self._log("ftl", next_id), lines)

    @tool(read_only=True, idempotent=True)
    async def webserver(self, next_id: _NextId = None, lines: _Lines = None) -> LogResponse:
        """Fetch the newest lines of the web server's log.

        It logs the web server's startup, TLS and errors, and each request it
        serves when FTL's `debug.api` setting is on. Use it when the web
        interface or the API doesn't answer as expected. Pi-hole keeps the last
        512 lines. Session IDs in requests read as `<redacted>`. It changes
        nothing.

        Args:
            next_id: `next_id` from an earlier call, to get only the lines
                written since, for polling: with nothing new, no lines. Leave
                it out to get every line kept, and again when a call returns
                a lower `next_id` than it was given: the log started over.
            lines: How many of the newest lines to return, at least 1. All of
                them by default.
        """
        return _clean(await self._log("webserver", next_id), lines)
