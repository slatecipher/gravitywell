"""Models for the DNS control endpoints, under `/dns`."""

from typing import Literal

from pydantic import Field

from gravitywell.models._base import BaseResponse


class BlockingResponse(BaseResponse):
    """Whether the Pi-hole is blocking ads and trackers, and for how long."""

    # FTL sends `failure`, though its API spec says `failed`: accept both.
    blocking: Literal["enabled", "disabled", "failure", "failed", "unknown"] = Field(
        description=(
            "The status: `enabled` (blocking), `disabled` (letting every domain through), `failure` (the DNS server "
            "isn't running, so nothing is answered; the API's spec calls it `failed`) or `unknown` (not known yet, "
            "such as while the Pi-hole starts)."
        )
    )
    timer: float | None = Field(
        description=(
            "Seconds until the status switches back on its own, such as `299.5`, or `null` if the status is permanent."
        )
    )
