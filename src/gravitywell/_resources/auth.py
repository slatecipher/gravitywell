"""The session endpoints, under `/auth`.

Logging in and out is `PiHoleAuth`'s job: these list and end sessions.
"""

from clientx import AsyncResource, Resource, method

from gravitywell.models import ActiveSessionsResponse


class Sessions(Resource, prefix="/auth", tags=["sessions"]):
    """The sessions logged in to the Pi-hole's API."""

    @method.delete("/session/{session_id}")
    def delete(self, session_id: int) -> None:
        """Log out a session, by its number from the session list.

        Whoever holds it is logged out: a browser has to log in again, and an
        app or script logs in again on its next request, if it can. Use it to
        free sessions apps left open, as the Pi-hole allows only so many.
        Deleting this client's own session (`current_session`) only makes it
        log in again. A number not in use answers with an error (400).
        With an application password, it answers with an error (403) unless
        the Pi-hole's `webserver.api.app_sudo` setting is on.

        Args:
            session_id: The session's number, its `id` in the list, such as
                `3`.
        """
        ...

    @method.get("/sessions")
    def list(self) -> ActiveSessionsResponse:
        """List the sessions logged in to the Pi-hole's API.

        Each is a browser on the web interface, an app or script with an
        application password, or the Pi-hole's command line, with where it
        logged in from and when it was last active. Use it to find sessions
        to log out, such as ones apps left open: the Pi-hole allows only 16 at
        once by default. It never shows a session's secret ID. It changes
        nothing.
        With an application password, it answers with an error (403) unless
        the Pi-hole's `webserver.api.app_sudo` setting is on.
        """
        ...


class AsyncSessions(AsyncResource, prefix="/auth", tags=["sessions"]):
    """The sessions logged in to the Pi-hole's API."""

    @method.delete("/session/{session_id}")
    async def delete(self, session_id: int) -> None:
        """Log out a session, by its number from the session list.

        Whoever holds it is logged out: a browser has to log in again, and an
        app or script logs in again on its next request, if it can. Use it to
        free sessions apps left open, as the Pi-hole allows only so many.
        Deleting this client's own session (`current_session`) only makes it
        log in again. A number not in use answers with an error (400).
        With an application password, it answers with an error (403) unless
        the Pi-hole's `webserver.api.app_sudo` setting is on.

        Args:
            session_id: The session's number, its `id` in the list, such as
                `3`.
        """
        ...

    @method.get("/sessions")
    async def list(self) -> ActiveSessionsResponse:
        """List the sessions logged in to the Pi-hole's API.

        Each is a browser on the web interface, an app or script with an
        application password, or the Pi-hole's command line, with where it
        logged in from and when it was last active. Use it to find sessions
        to log out, such as ones apps left open: the Pi-hole allows only 16 at
        once by default. It never shows a session's secret ID. It changes
        nothing.
        With an application password, it answers with an error (403) unless
        the Pi-hole's `webserver.api.app_sudo` setting is on.
        """
        ...
