"""Secret-safe configuration for the API-Football client."""

from __future__ import annotations

import os
from collections.abc import Mapping
from urllib.parse import urlparse

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError
from pydantic.functional_validators import field_validator

from football_copilot.api_football.errors import ApiFootballConfigurationError

DEFAULT_BASE_URL = "https://v3.football.api-sports.io"
DEFAULT_TIMEOUT_SECONDS = 15.0


class ApiFootballConfig(BaseModel):
    """Validated settings whose representation never includes the API key."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    api_key: SecretStr = Field(repr=False)
    base_url: str = DEFAULT_BASE_URL
    timeout_seconds: float = Field(default=DEFAULT_TIMEOUT_SECONDS, gt=0, le=300)

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, value: SecretStr) -> SecretStr:
        secret = value.get_secret_value().strip()
        if not secret:
            raise ValueError("API_FOOTBALL_KEY is missing")
        return SecretStr(secret)

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        normalized = value.strip().rstrip("/")
        parsed = urlparse(normalized)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("API_FOOTBALL_BASE_URL must be an HTTP(S) URL")
        return normalized


def load_api_football_config(
    environment: Mapping[str, str] | None = None,
) -> ApiFootballConfig:
    """Load settings from a supplied mapping or the local environment and `.env`."""

    if environment is None:
        load_dotenv()
        environment = os.environ

    try:
        return ApiFootballConfig(
            api_key=SecretStr(environment.get("API_FOOTBALL_KEY", "")),
            base_url=environment.get("API_FOOTBALL_BASE_URL", DEFAULT_BASE_URL),
            timeout_seconds=environment.get(
                "API_FOOTBALL_TIMEOUT_SECONDS",
                str(DEFAULT_TIMEOUT_SECONDS),
            ),
        )
    except ValidationError:
        raise ApiFootballConfigurationError(
            "API-Football configuration is missing or invalid"
        ) from None
