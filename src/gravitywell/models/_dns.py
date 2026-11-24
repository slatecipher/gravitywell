"""Models for the DNS control endpoints, under `/dns`."""

from pydantic import Field

from gravitywell.models._base import BLOCKING_STATUS, BaseResponse, BlockingStatus


class BlockingResponse(BaseResponse):
    """Whether the Pi-hole is blocking ads and trackers, and for how long."""

    blocking: BlockingStatus = Field(description=BLOCKING_STATUS)
    timer: float | None = Field(
        description=(
            "Seconds until the status switches back on its own, such as `299.5`, or `null` if the status is permanent."
        )
    )
