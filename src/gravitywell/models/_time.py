"""The time range that the query database endpoints take."""

from datetime import UTC, datetime
from typing import Annotated, Self

from pydantic import AfterValidator, BaseModel, Field, PlainSerializer, model_validator


def _require_timezone(value: datetime) -> datetime:
    if value.tzinfo is None:
        msg = "needs a timezone, such as `Z` or `+01:00`"
        raise ValueError(msg)
    return value


def _unix_seconds(value: datetime) -> int:
    return int(value.timestamp())


def _now() -> datetime:
    return datetime.now(UTC)


# A `datetime`, sent to Pi-hole as Unix seconds. Not Pydantic's `AwareDatetime`:
# ClientX spreads only plain values, such as `datetime`, into a query string.
_UnixTime = Annotated[datetime, AfterValidator(_require_timezone), PlainSerializer(_unix_seconds, return_type=int)]


class TimeRange(BaseModel):
    """A time range in the Pi-hole's query database.

    The database keeps queries for 91 days by default, and gets each one
    within about a minute. Both times need a timezone.
    """

    start: _UnixTime = Field(
        serialization_alias="from",
        description="When the range starts, with a timezone, such as `2026-11-24T00:00:00Z`.",
    )
    until: _UnixTime = Field(
        default_factory=_now,
        description="When the range ends, with a timezone, such as `2026-11-25T00:00:00+01:00`. Now by default.",
    )

    @model_validator(mode="after")
    def _start_before_until(self) -> Self:
        if self.start >= self.until:
            msg = "`start` must be before `until`"
            raise ValueError(msg)
        return self
