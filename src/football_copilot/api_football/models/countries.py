"""Country models used by API-Football reference-data responses."""

from pydantic import StrictStr

from football_copilot.api_football.models.common import UpstreamModel


class Country(UpstreamModel):
    name: StrictStr
    code: StrictStr | None = None
    flag: StrictStr | None = None
