"""The base of every response body model."""

from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """The fields every Pi-hole response body has."""

    took: float = Field(description="Seconds the Pi-hole took to process the request.")
