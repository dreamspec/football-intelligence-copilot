"""A small, secret-safe probe for learning the API-Football contract."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from typing import Any

import httpx
from dotenv import load_dotenv

BASE_URL = "https://v3.football.api-sports.io"
ALLOWED_ENDPOINTS = ("countries", "leagues", "standings", "teams", "fixtures")


class ProbeError(RuntimeError):
    """Raised when the probe cannot produce a trustworthy result."""


@dataclass(frozen=True)
class QuotaSnapshot:
    daily_limit: str | None
    daily_remaining: str | None
    minute_limit: str | None
    minute_remaining: str | None


@dataclass(frozen=True)
class ProbeResult:
    endpoint: str
    parameters: dict[str, str]
    status_code: int
    get: str | None
    results: int | None
    errors: Any
    paging: Any
    quota: QuotaSnapshot
    response_sample: Any

    def safe_dict(self) -> dict[str, Any]:
        """Return printable fields; the API key is intentionally not stored."""

        return asdict(self)


def parse_parameter(raw: str) -> tuple[str, str]:
    """Parse a CLI `key=value` parameter without guessing its data type."""

    key, separator, value = raw.partition("=")
    if not separator or not key.strip() or not value.strip():
        raise argparse.ArgumentTypeError("parameters must use non-empty key=value")
    return key.strip(), value.strip()


def parameters_to_dict(items: Sequence[tuple[str, str]]) -> dict[str, str]:
    """Convert parsed parameters to a dictionary and reject duplicate keys."""

    parameters: dict[str, str] = {}
    for key, value in items:
        if key in parameters:
            raise ProbeError(f"duplicate parameter: {key}")
        parameters[key] = value
    return parameters


def read_quota(headers: httpx.Headers) -> QuotaSnapshot:
    """Extract the daily and per-minute quota counters returned by API-Sports."""

    return QuotaSnapshot(
        daily_limit=headers.get("x-ratelimit-requests-limit"),
        daily_remaining=headers.get("x-ratelimit-requests-remaining"),
        minute_limit=headers.get("x-ratelimit-limit"),
        minute_remaining=headers.get("x-ratelimit-remaining"),
    )


def probe_endpoint(
    endpoint: str,
    *,
    parameters: dict[str, str] | None = None,
    api_key: str,
    transport: httpx.BaseTransport | None = None,
) -> ProbeResult:
    """Call one allow-listed endpoint and return a secret-free summary."""

    if endpoint not in ALLOWED_ENDPOINTS:
        raise ProbeError(f"unsupported probe endpoint: {endpoint}")
    if not api_key.strip():
        raise ProbeError("API_FOOTBALL_KEY is missing; add it to the local .env file")

    safe_parameters = dict(parameters or {})
    try:
        with httpx.Client(
            base_url=BASE_URL,
            headers={"x-apisports-key": api_key},
            timeout=15.0,
            transport=transport,
        ) as client:
            response = client.get(f"/{endpoint}", params=safe_parameters)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise ProbeError(f"API-Football returned HTTP {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise ProbeError(f"could not reach API-Football: {type(exc).__name__}") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise ProbeError("API-Football returned a non-JSON response") from exc

    if not isinstance(payload, dict):
        raise ProbeError("API-Football returned an unexpected JSON shape")

    api_errors = payload.get("errors")
    if api_errors not in (None, [], {}):
        raise ProbeError(f"API-Football reported an API-level error: {api_errors}")

    response_data = payload.get("response")
    if isinstance(response_data, list):
        response_sample = response_data[:1]
    else:
        response_sample = response_data

    return ProbeResult(
        endpoint=endpoint,
        parameters=safe_parameters,
        status_code=response.status_code,
        get=payload.get("get"),
        results=payload.get("results"),
        errors=api_errors,
        paging=payload.get("paging"),
        quota=read_quota(response.headers),
        response_sample=response_sample,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect one API-Football response without printing the API key."
    )
    parser.add_argument("endpoint", choices=ALLOWED_ENDPOINTS)
    parser.add_argument(
        "--param",
        action="append",
        default=[],
        type=parse_parameter,
        metavar="KEY=VALUE",
        help="repeatable API query parameter",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    load_dotenv()
    args = build_parser().parse_args(argv)
    try:
        parameters = parameters_to_dict(args.param)
        result = probe_endpoint(
            args.endpoint,
            parameters=parameters,
            api_key=os.getenv("API_FOOTBALL_KEY", ""),
        )
    except ProbeError as exc:
        print(f"Probe failed: {exc}")
        return 1

    print(json.dumps(result.safe_dict(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
