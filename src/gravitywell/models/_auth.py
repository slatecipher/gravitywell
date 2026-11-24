"""Models for the authentication endpoints, under `/auth`."""

from pydantic import BaseModel, Field

from gravitywell.models._base import BaseResponse


class Session(BaseModel):
    """A login session on the Pi-hole."""

    sid: str | None = Field(description="The session ID, or `null` if the Pi-hole has no password.")


class SessionResponse(BaseResponse):
    """The Pi-hole's answer to a login."""

    session: Session
