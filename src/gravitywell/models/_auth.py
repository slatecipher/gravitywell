"""Models for the authentication endpoints, under `/auth`."""

from datetime import datetime

from pydantic import BaseModel, Field

from gravitywell.models._base import BaseResponse


class Session(BaseModel):
    """A login session on the Pi-hole."""

    sid: str | None = Field(description="The session ID, or `null` if the Pi-hole has no password.")


class SessionResponse(BaseResponse):
    """The Pi-hole's answer to a login."""

    session: Session


class SessionTls(BaseModel):
    """Whether a session used HTTPS."""

    login: bool = Field(description="Whether it logged in over HTTPS.")
    mixed: bool = Field(description="Whether it has since been used over plain HTTP as well.")


class ActiveSession(BaseModel):
    """A session logged in to the Pi-hole's API."""

    id: int = Field(
        description="The session's number, to delete it by. It isn't the secret session ID, which is never listed."
    )
    current_session: bool = Field(description="Whether it's the session making this request: this client's own.")
    valid: bool = Field(description="Whether it's still valid, rather than expired.")
    tls: SessionTls
    login_at: datetime = Field(description="When it logged in, in UTC.")
    last_active: datetime = Field(description="When it last made a request, in UTC.")
    valid_until: datetime = Field(description="When it expires unless used again, in UTC.")
    remote_addr: str = Field(description="The IP address it logged in from.")
    user_agent: str | None = Field(description="The browser or program that logged in, as it named itself.")
    x_forwarded_for: str | None = Field(
        description="The original client's address, if it came through a proxy that said so, or `null`."
    )
    app: bool = Field(description="Whether it logged in with an application password, as an app or script does.")
    cli: bool = Field(description="Whether it's the Pi-hole's own command line, `pihole`.")


class ActiveSessionsResponse(BaseResponse):
    """The sessions logged in to the Pi-hole's API."""

    sessions: list[ActiveSession] = Field(
        description="The sessions. The Pi-hole allows `webserver.api.max_sessions`, 16 by default, at once."
    )
