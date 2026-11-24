"""Models for the action endpoints, under `/action`."""

from pydantic import BaseModel, Field


class GravityUpdate(BaseModel):
    """The result of a gravity update, read from the text Pi-hole sends."""

    output: str = Field(
        description="What `pihole -g` printed: each step, and for each list its URL, download status and domain "
        "count, such as `[✓] Status: No changes detected`."
    )
    succeeded: bool = Field(
        description="Whether the update finished without an error. When `false`, `output` ends with `Gravity "
        "failed`, and its `[✗]` lines say what went wrong."
    )
