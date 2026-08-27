"""Typed boundary for the API-Football REST service."""

from football_copilot.api_football.client import ApiFootballClient
from football_copilot.api_football.config import (
    ApiFootballConfig,
    load_api_football_config,
)
from football_copilot.api_football.models.countries import Country
from football_copilot.api_football.models.leagues import LeagueRecord, LeaguesQuery

__all__ = [
    "ApiFootballClient",
    "ApiFootballConfig",
    "Country",
    "LeagueRecord",
    "LeaguesQuery",
    "load_api_football_config",
]
