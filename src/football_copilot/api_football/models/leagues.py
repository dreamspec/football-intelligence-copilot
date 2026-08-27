"""Request and response models for the API-Football leagues resource."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr

from football_copilot.api_football.models.common import UpstreamModel
from football_copilot.api_football.models.countries import Country

SeasonYear = Annotated[StrictInt, Field(ge=1900, le=9999)]


class LeaguesQuery(BaseModel):
    """The smallest league query needed by the first production client slice."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        str_strip_whitespace=True,
    )

    country: StrictStr = Field(min_length=1)
    season: SeasonYear

    def as_query_params(self) -> dict[str, str]:
        return {"country": self.country, "season": str(self.season)}


class FixtureCoverage(UpstreamModel):
    events: StrictBool | None = None
    lineups: StrictBool | None = None
    statistics_fixtures: StrictBool | None = None
    statistics_players: StrictBool | None = None


class LeagueCoverage(UpstreamModel):
    fixtures: FixtureCoverage | None = None
    standings: StrictBool | None = None
    players: StrictBool | None = None
    top_scorers: StrictBool | None = None
    top_assists: StrictBool | None = None
    top_cards: StrictBool | None = None
    injuries: StrictBool | None = None
    predictions: StrictBool | None = None
    odds: StrictBool | None = None


class LeagueSeason(UpstreamModel):
    year: SeasonYear
    start: date
    end: date
    current: StrictBool
    coverage: LeagueCoverage


class LeagueSummary(UpstreamModel):
    id: StrictInt
    name: StrictStr
    type: StrictStr
    logo: StrictStr | None = None


class LeagueRecord(UpstreamModel):
    league: LeagueSummary
    country: Country
    seasons: list[LeagueSeason]
