"""Models for the log endpoints, under `/logs`."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from gravitywell.models._base import BaseResponse


class LogLine(BaseModel):
    """A line of one of the Pi-hole's logs."""

    timestamp: datetime = Field(description="When it was written, in UTC.")
    message: str = Field(description="The line's text, cut short after 259 characters.")
    prio: str | None = Field(
        description="Its priority, in FTL's log: `INFO`, `NOTICE`, `WARNING`, `ERROR`, `CRIT`, `ALERT` or `EMERG`, "
        "or the debug setting that wrote it, such as `DEBUG_API`. `null` in the dnsmasq and web server logs."
    )


class LogResponse(BaseResponse):
    """The newest lines of one of the Pi-hole's logs, the oldest first."""

    # Pi-hole's `nextID`, or `next_id`, which a dump or an AI tool's result
    # uses.
    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)

    log: list[LogLine] = Field(description="The lines, the oldest first.")
    next_id: int = Field(
        alias="nextID", description="Pass it as `next_id` on the next call to get only the lines written since."
    )
    pid: int = Field(
        description="FTL's process ID. When it changes, FTL restarted: call again without `next_id` to read the log "
        "from its start."
    )
    file: str = Field(description="The log file's path on the Pi-hole's machine, such as `/var/log/pihole/FTL.log`.")
