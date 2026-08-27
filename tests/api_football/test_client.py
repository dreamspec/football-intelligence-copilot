from __future__ import annotations

from datetime import UTC, date, datetime

import httpx
import pytest
from pydantic import SecretStr, ValidationError

from football_copilot.api_football.client import ApiFootballClient
from football_copilot.api_football.config import (
    ApiFootballConfig,
    load_api_football_config,
)
from football_copilot.api_football.errors import (
    ApiFootballApiError,
    ApiFootballConfigurationError,
    ApiFootballHttpError,
    ApiFootballRequestError,
    ApiFootballSchemaError,
)
from football_copilot.api_football.models.countries import Country
from football_copilot.api_football.models.leagues import LeaguesQuery

pytestmark = pytest.mark.anyio

FIXED_TIME = datetime(2026, 8, 19, 12, 30, tzinfo=UTC)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def config() -> ApiFootballConfig:
    return ApiFootballConfig(
        api_key=SecretStr("super-secret"),
        base_url="https://api-football.test",
    )


def quota_headers(*, daily_remaining: str = "99") -> dict[str, str]:
    return {
        "x-ratelimit-requests-limit": "100",
        "x-ratelimit-requests-remaining": daily_remaining,
        "x-ratelimit-limit": "10",
        "x-ratelimit-remaining": "9",
    }


def test_configuration_is_validated_without_exposing_the_key() -> None:
    config = load_api_football_config(
        {
            "API_FOOTBALL_KEY": " super-secret ",
            "API_FOOTBALL_TIMEOUT_SECONDS": "20",
        }
    )

    assert config.api_key.get_secret_value() == "super-secret"
    assert config.timeout_seconds == 20
    assert "super-secret" not in repr(config)
    assert "super-secret" not in str(config)

    with pytest.raises(ApiFootballConfigurationError, match="missing or invalid"):
        load_api_football_config({})


def test_leagues_query_rejects_untyped_or_invalid_arguments() -> None:
    assert LeaguesQuery(country=" England ", season=2024).as_query_params() == {
        "country": "England",
        "season": "2024",
    }

    with pytest.raises(ValidationError):
        LeaguesQuery.model_validate({"country": "England", "season": "2024"})

    with pytest.raises(ValidationError):
        LeaguesQuery(country="", season=2024)

    with pytest.raises(ValidationError):
        LeaguesQuery.model_validate(
            {"country": "England", "season": 2024, "unexpected": True}
        )


async def test_countries_response_is_typed_and_forward_compatible(
    config: ApiFootballConfig,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/countries"
        assert not request.url.params
        assert request.headers["x-apisports-key"] == "super-secret"
        return httpx.Response(
            200,
            headers=quota_headers(),
            json={
                "get": "countries",
                "parameters": [],
                "errors": [],
                "results": 1,
                "paging": {"current": 1, "total": 1},
                "response": [
                    {
                        "name": "England",
                        "code": "GB-ENG",
                        "flag": "https://example.test/england.svg",
                        "new_upstream_field": "ignored",
                    }
                ],
                "new_envelope_field": "ignored",
            },
        )

    client = ApiFootballClient(
        config,
        transport=httpx.MockTransport(handler),
        clock=lambda: FIXED_TIME,
    )
    async with client:
        result = await client.get_countries()

    assert client.is_closed
    assert result.response == [
        Country(
            name="England",
            code="GB-ENG",
            flag="https://example.test/england.svg",
        )
    ]
    assert result.quota.daily_remaining == 99
    assert result.retrieved_at == FIXED_TIME
    assert not hasattr(result.response[0], "new_upstream_field")
    assert "super-secret" not in repr(result)


async def test_leagues_query_and_nested_response_are_typed(
    config: ApiFootballConfig,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert dict(request.url.params) == {
            "country": "England",
            "season": "2024",
        }
        return httpx.Response(
            200,
            headers=quota_headers(daily_remaining="98"),
            json={
                "get": "leagues",
                "parameters": {"country": "England", "season": "2024"},
                "errors": [],
                "results": 1,
                "paging": {"current": 1, "total": 1},
                "response": [
                    {
                        "league": {
                            "id": 39,
                            "name": "Premier League",
                            "type": "League",
                            "logo": "https://example.test/premier-league.png",
                        },
                        "country": {
                            "name": "England",
                            "code": "GB-ENG",
                            "flag": "https://example.test/england.svg",
                        },
                        "seasons": [
                            {
                                "year": 2024,
                                "start": "2024-08-16",
                                "end": "2025-05-25",
                                "current": False,
                                "coverage": {
                                    "fixtures": {
                                        "events": True,
                                        "lineups": True,
                                        "statistics_fixtures": True,
                                        "statistics_players": True,
                                    },
                                    "standings": True,
                                    "players": True,
                                    "top_scorers": True,
                                    "top_assists": True,
                                    "top_cards": True,
                                    "injuries": True,
                                    "predictions": True,
                                    "odds": False,
                                },
                            }
                        ],
                    }
                ],
            },
        )

    async with ApiFootballClient(
        config,
        transport=httpx.MockTransport(handler),
        clock=lambda: FIXED_TIME,
    ) as client:
        result = await client.get_leagues(
            LeaguesQuery(country="England", season=2024)
        )

    record = result.response[0]
    season = record.seasons[0]
    assert record.league.id == 39
    assert season.start == date(2024, 8, 16)
    assert season.coverage.fixtures is not None
    assert season.coverage.fixtures.lineups is True
    assert season.coverage.odds is False
    assert result.quota.daily_remaining == 98


async def test_api_level_errors_preserve_quota_and_redact_the_key(
    config: ApiFootballConfig,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers=quota_headers(daily_remaining="97"),
            json={
                "get": "leagues",
                "parameters": {"country": "England", "season": "2025"},
                "errors": {
                    "plan": "super-secret cannot access the requested season"
                },
                "results": 0,
                "paging": {"current": 1, "total": 1},
                "response": [],
            },
        )

    async with ApiFootballClient(
        config,
        transport=httpx.MockTransport(handler),
    ) as client:
        with pytest.raises(ApiFootballApiError) as caught:
            await client.get_leagues(LeaguesQuery(country="England", season=2025))

    error = caught.value
    assert error.quota.daily_remaining == 97
    assert error.details == {
        "plan": "[REDACTED] cannot access the requested season"
    }
    assert "super-secret" not in str(error)


async def test_http_errors_are_safe_and_preserve_quota(
    config: ApiFootballConfig,
) -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            429,
            headers=quota_headers(daily_remaining="0"),
            text="untrusted upstream body",
        )
    )

    async with ApiFootballClient(config, transport=transport) as client:
        with pytest.raises(ApiFootballHttpError) as caught:
            await client.get_countries()

    assert caught.value.status_code == 429
    assert caught.value.quota.daily_remaining == 0
    assert "untrusted upstream body" not in str(caught.value)


async def test_transport_errors_do_not_leak_httpx_exceptions(
    config: ApiFootballConfig,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection details", request=request)

    async with ApiFootballClient(
        config,
        transport=httpx.MockTransport(handler),
    ) as client:
        with pytest.raises(ApiFootballRequestError, match="ConnectError") as caught:
            await client.get_countries()

    assert caught.value.__cause__ is None
    assert "connection details" not in str(caught.value)


async def test_non_json_response_raises_a_safe_schema_error(
    config: ApiFootballConfig,
) -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            headers=quota_headers(),
            text="not JSON and not safe to echo",
        )
    )

    async with ApiFootballClient(config, transport=transport) as client:
        with pytest.raises(ApiFootballSchemaError, match="non-JSON") as caught:
            await client.get_countries()

    assert "not safe to echo" not in str(caught.value)


@pytest.mark.parametrize(
    "payload",
    [
        ["not", "an", "object"],
        {
            "get": "countries",
            "parameters": [],
            "errors": [],
            "results": 1,
            "paging": {"current": 1, "total": 1},
            "response": [{"code": "GB-ENG"}],
        },
        {
            "get": "unexpected",
            "parameters": [],
            "errors": [],
            "results": 0,
            "paging": {"current": 1, "total": 1},
            "response": [],
        },
    ],
)
async def test_invalid_response_shapes_raise_safe_schema_errors(
    config: ApiFootballConfig,
    payload: object,
) -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, headers=quota_headers(), json=payload)
    )

    async with ApiFootballClient(config, transport=transport) as client:
        with pytest.raises(ApiFootballSchemaError, match="countries") as caught:
            await client.get_countries()

    assert caught.value.__cause__ is None
    assert "GB-ENG" not in str(caught.value)
