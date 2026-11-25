"""Session authentication for a Pi-hole."""

import threading
from collections.abc import AsyncGenerator, Callable, Generator
from contextlib import suppress
from dataclasses import dataclass

import anyio
import httpx2

from gravitywell.models import Session, SessionResponse

_SID_HEADER = "X-FTL-SID"
# A request is sent once, and once more after a 401 with a new login.
_ATTEMPTS = 2
_AUTH_PATH = "/api/auth"

type PasswordProvider = Callable[[], str]


@dataclass(frozen=True)
class _Login:
    """A session, with the URL that issued it, where logging out goes."""

    session: Session
    url: httpx2.URL


class PiHoleAuth(httpx2.Auth):
    """Log in to a Pi-hole with a password, and send its session on requests.

    Pass it as a client's `auth=`:

        with PiHole("http://pi.hole", auth=PiHoleAuth(password)) as api:
            api.info.version()

    It logs in before the first request (`POST /api/auth`), sends the session in
    the `X-FTL-SID` header, and logs in again once if a request gets a 401.
    Concurrent requests share one login, since a Pi-hole allows only a few
    sessions at a time. A failed login raises `httpx2.HTTPStatusError` with
    the login's response. The clients log out when they close.

    Use an application password, which Pi-hole's settings create. Two-factor
    authentication isn't supported. To read the password at each login, such
    as from a secret file that's replaced when it changes, pass a function
    that returns it: `PiHoleAuth(lambda: path.read_text().strip())`. Async
    clients call it in the event loop, so it should be quick.
    """

    def __init__(self, password: str | PasswordProvider) -> None:
        self._password = password
        # None until logged in. A session whose sid is None means the Pi-hole
        # has no password, so no header is sent.
        self._login: _Login | None = None
        self._sync_lock = threading.Lock()
        self._async_lock = anyio.Lock()

    def sync_auth_flow(self, request: httpx2.Request) -> Generator[httpx2.Request, httpx2.Response, None]:
        rejected: _Login | None = None
        for _ in range(_ATTEMPTS):
            with self._sync_lock:
                # Log in if there's no session, or if this request's session
                # was rejected and no other request has logged in again since.
                if self._login is None or self._login is rejected:
                    login_response = yield self._login_request(request)
                    login_response.read()
                    self._login = _login_from(login_response)
                login = self._login
            _send_session(request, login.session)
            response = yield request
            if response.status_code != 401:
                return
            rejected = login

    async def async_auth_flow(self, request: httpx2.Request) -> AsyncGenerator[httpx2.Request, httpx2.Response]:
        rejected: _Login | None = None
        for _ in range(_ATTEMPTS):
            async with self._async_lock:
                # Log in if there's no session, or if this request's session
                # was rejected and no other request has logged in again since.
                if self._login is None or self._login is rejected:
                    login_response = yield self._login_request(request)
                    await login_response.aread()
                    self._login = _login_from(login_response)
                login = self._login
            _send_session(request, login.session)
            response = yield request
            if response.status_code != 401:
                return
            rejected = login

    def log_out(self, client: httpx2.Client) -> None:
        """Log out of the session through `client`, if there is one.

        The clients call it when they close. A failed logout is ignored: the
        session expires on its own.
        """
        login, self._login = self._login, None
        if login is not None and login.session.sid is not None:
            with suppress(httpx2.HTTPError):
                client.delete(login.url, headers={_SID_HEADER: login.session.sid}, auth=httpx2.Auth())

    async def alog_out(self, client: httpx2.AsyncClient) -> None:
        """Log out of the session through `client`, if there is one.

        The async clients call it when they close. A failed logout is ignored:
        the session expires on its own.
        """
        login, self._login = self._login, None
        if login is not None and login.session.sid is not None:
            with suppress(httpx2.HTTPError):
                await client.delete(login.url, headers={_SID_HEADER: login.session.sid}, auth=httpx2.Auth())

    def _login_request(self, request: httpx2.Request) -> httpx2.Request:
        # Requests made in an auth flow skip the client's default headers.
        user_agent = request.headers.get("User-Agent")
        headers = {"User-Agent": user_agent} if user_agent is not None else None
        login_url = request.url.copy_with(path=_AUTH_PATH)
        password = self._password if isinstance(self._password, str) else self._password()
        return httpx2.Request("POST", login_url, json={"password": password}, headers=headers)


def _login_from(response: httpx2.Response) -> _Login:
    """Read the session, raising `httpx2.HTTPStatusError` for a failed login."""
    response.raise_for_status()
    body = SessionResponse.model_validate_json(response.content)
    return _Login(body.session, response.request.url)


def _send_session(request: httpx2.Request, session: Session) -> None:
    if session.sid is None:
        request.headers.pop(_SID_HEADER, None)
    else:
        request.headers[_SID_HEADER] = session.sid
