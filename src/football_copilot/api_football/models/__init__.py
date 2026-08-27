"""Typed request and response models for API-Football resources."""

from football_copilot.api_football.models.common import (
    ApiFootballResponse,
    Paging,
    QuotaSnapshot,
)
from football_copilot.api_football.models.countries import Country
from football_copilot.api_football.models.leagues import LeagueRecord, LeaguesQuery

__all__ = [
    "ApiFootballResponse",
    "Country",
    "LeagueRecord",
    "LeaguesQuery",
    "Paging",
    "QuotaSnapshot",
]
