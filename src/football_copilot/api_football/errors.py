"""Small, secret-safe exception boundary for the typed API client."""

from __future__ import annotations

from typing import Any

from football_copilot.api_football.models.common import QuotaSnapshot


class ApiFootballError(RuntimeError):
    """Base class for failures exposed by the API-Football boundary."""


class ApiFootballConfigurationError(ApiFootballError):
    """Raised when local API-Football configuration is unusable."""


class ApiFootballRequestError(ApiFootballError):
    """Raised when a request cannot reach API-Football."""


class ApiFootballHttpError(ApiFootballError):
    """Raised for a non-successful HTTP response."""

    def __init__(self, status_code: int, quota: QuotaSnapshot) -> None:
        self.status_code = status_code
        self.quota = quota
        super().__init__(f"API-Football returned HTTP {status_code}")


class ApiFootballApiError(ApiFootballError):
    """Raised when API-Football reports errors inside a successful HTTP response."""

    def __init__(self, details: Any, quota: QuotaSnapshot) -> None:
        self.details = details
        self.quota = quota
        super().__init__(f"API-Football reported an API-level error: {details}")


class ApiFootballSchemaError(ApiFootballError):
    """Raised when the upstream JSON does not match the modeled contract."""


def redact_secret(value: Any, secret: str) -> Any:
    """Return a recursively copied value with the credential removed from strings."""

    if isinstance(value, str):
        return value.replace(secret, "[REDACTED]") if secret else value
    if isinstance(value, list):
        return [redact_secret(item, secret) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_secret(item, secret) for item in value)
    if isinstance(value, dict):
        return {
            redact_secret(key, secret) if isinstance(key, str) else key: redact_secret(
                item, secret
            )
            for key, item in value.items()
        }
    return value
