from __future__ import annotations

import httpx
import pytest

from football_copilot.api_probe import (
    ProbeError,
    parameters_to_dict,
    parse_parameter,
    probe_endpoint,
)


def mock_transport(
    payload: dict,
    *,
    status_code: int = 200,
) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-apisports-key"] == "super-secret"
        return httpx.Response(
            status_code,
            json=payload,
            headers={
                "x-ratelimit-requests-limit": "100",
                "x-ratelimit-requests-remaining": "99",
                "x-ratelimit-limit": "10",
                "x-ratelimit-remaining": "9",
            },
        )

    return httpx.MockTransport(handler)


def test_probe_returns_safe_response_summary_without_secret() -> None:
    transport = mock_transport(
        {
            "get": "countries",
            "parameters": [],
            "errors": [],
            "results": 2,
            "paging": {"current": 1, "total": 1},
            "response": [{"name": "England"}, {"name": "India"}],
        }
    )

    result = probe_endpoint(
        "countries",
        api_key="super-secret",
        transport=transport,
    )

    assert result.results == 2
    assert result.response_sample == [{"name": "England"}]
    assert result.quota.daily_remaining == "99"
    assert "super-secret" not in str(result.safe_dict())


def test_probe_serializes_query_parameters() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["league"] == "39"
        assert request.url.params["season"] == "2025"
        return httpx.Response(
            200,
            json={
                "get": "standings",
                "errors": [],
                "results": 0,
                "paging": {"current": 1, "total": 1},
                "response": [],
            },
        )

    result = probe_endpoint(
        "standings",
        parameters={"league": "39", "season": "2025"},
        api_key="super-secret",
        transport=httpx.MockTransport(handler),
    )

    assert result.parameters == {"league": "39", "season": "2025"}
    assert result.results == 0


def test_api_level_error_inside_http_200_is_not_treated_as_success() -> None:
    transport = mock_transport(
        {
            "get": "standings",
            "errors": {"season": "The Season field is required."},
            "results": 0,
            "paging": {"current": 1, "total": 1},
            "response": [],
        }
    )

    with pytest.raises(ProbeError, match="API-level error"):
        probe_endpoint(
            "standings",
            api_key="super-secret",
            transport=transport,
        )


def test_missing_key_fails_before_network_request() -> None:
    with pytest.raises(ProbeError, match="API_FOOTBALL_KEY is missing"):
        probe_endpoint("countries", api_key="")


def test_parameter_parsing_and_duplicate_detection() -> None:
    assert parse_parameter(" season = 2025 ") == ("season", "2025")

    with pytest.raises(ProbeError, match="duplicate parameter"):
        parameters_to_dict([("season", "2025"), ("season", "2026")])

