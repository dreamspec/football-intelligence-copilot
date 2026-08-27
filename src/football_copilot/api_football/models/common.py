"""Common API-Football envelope and metadata models."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr
from pydantic.functional_validators import field_validator

NonNegativeInt = Annotated[StrictInt, Field(ge=0)]


class UpstreamModel(BaseModel):
    """Validate used fields while tolerating irrelevant additions upstream."""

    model_config = ConfigDict(
        extra="ignore",
        frozen=True,
        hide_input_in_errors=True,
    )


class Paging(UpstreamModel):
    current: NonNegativeInt
    total: NonNegativeInt


class QuotaSnapshot(BaseModel):
    """Quota counters observed on one response; this is not persistent tracking."""

    model_config = ConfigDict(frozen=True)

    daily_limit: int | None = None
    daily_remaining: int | None = None
    minute_limit: int | None = None
    minute_remaining: int | None = None


class ApiFootballResponse[ResponseItem](UpstreamModel):
    """Typed upstream envelope enriched with safe response metadata."""

    get: StrictStr
    parameters: dict[str, Any] | list[Any]
    errors: dict[str, Any] | list[Any] | None
    results: NonNegativeInt
    paging: Paging
    response: list[ResponseItem]
    quota: QuotaSnapshot
    retrieved_at: datetime

    @field_validator("retrieved_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("retrieved_at must include a timezone")
        return value
