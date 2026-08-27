"""Asynchronous, typed client for the small supported API-Football surface."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Self, TypeVar

import httpx
from pydantic import ValidationError

from football_copilot.api_football.config import ApiFootballConfig
from football_copilot.api_football.errors import (
    ApiFootballApiError,
    ApiFootballHttpError,
    ApiFootballRequestError,
    ApiFootballSchemaError,
    redact_secret,
)
from football_copilot.api_football.models.common import (
    ApiFootballResponse,
    QuotaSnapshot,
)
from football_copilot.api_football.models.countries import Country
from football_copilot.api_football.models.leagues import LeagueRecord, LeaguesQuery

ResponseItem = TypeVar("ResponseItem")


def utc_now() -> datetime:
    return datetime.now(UTC)


def read_quota(headers: httpx.Headers) -> QuotaSnapshot:
    """Extract numeric quota counters without failing on a malformed optional header."""

    def optional_int(name: str) -> int | None:
        value = headers.get(name)
        if value is None:
            return None
        try:
            return int(value)
        except ValueError:
            return None

    return QuotaSnapshot(
        daily_limit=optional_int("x-ratelimit-requests-limit"),
        daily_remaining=optional_int("x-ratelimit-requests-remaining"),
        minute_limit=optional_int("x-ratelimit-limit"),
        minute_remaining=optional_int("x-ratelimit-remaining"),
    )


class ApiFootballClient:
    """Own HTTP, authentication, and validation for supported football resources."""

    def __init__(
        self,
        config: ApiFootballConfig,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._api_key = config.api_key.get_secret_value()
        self._clock = clock
        self._http = httpx.AsyncClient(
            base_url=config.base_url,
            headers={"x-apisports-key": self._api_key},
            timeout=config.timeout_seconds,
            transport=transport,
        )

    @property
    def is_closed(self) -> bool:
        return self._http.is_closed

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._http.aclose()

    async def get_countries(self) -> ApiFootballResponse[Country]:
        return await self._get(
            endpoint="countries",
            parameters={},
            response_model=ApiFootballResponse[Country],
        )

    async def get_leagues(
        self,
        query: LeaguesQuery,
    ) -> ApiFootballResponse[LeagueRecord]:
        return await self._get(
            endpoint="leagues",
            parameters=query.as_query_params(),
            response_model=ApiFootballResponse[LeagueRecord],
        )

    async def _get(
        self,
        *,
        endpoint: str,
        parameters: dict[str, str],
        response_model: type[ApiFootballResponse[ResponseItem]],
    ) -> ApiFootballResponse[ResponseItem]:
        try:
            response = await self._http.get(f"/{endpoint}", params=parameters)
        except httpx.RequestError as exc:
            raise ApiFootballRequestError(
                f"could not reach API-Football: {type(exc).__name__}"
            ) from None

        quota = read_quota(response.headers)
        if not response.is_success:
            raise ApiFootballHttpError(response.status_code, quota)

        try:
            payload = response.json()
        except ValueError:
            raise ApiFootballSchemaError(
                f"API-Football returned non-JSON data for {endpoint}"
            ) from None

        if not isinstance(payload, dict):
            raise ApiFootballSchemaError(
                f"API-Football returned an invalid {endpoint} response"
            )

        api_errors = payload.get("errors")
        if api_errors not in (None, [], {}):
            safe_errors = redact_secret(api_errors, self._api_key)
            raise ApiFootballApiError(safe_errors, quota)

        enriched_payload = {
            **payload,
            "quota": quota,
            "retrieved_at": self._clock(),
        }
        try:
            parsed = response_model.model_validate(enriched_payload)
        except ValidationError:
            raise ApiFootballSchemaError(
                f"API-Football returned an invalid {endpoint} response"
            ) from None

        if parsed.get != endpoint:
            raise ApiFootballSchemaError(
                f"API-Football returned an unexpected endpoint for {endpoint}"
            )
        return parsed
