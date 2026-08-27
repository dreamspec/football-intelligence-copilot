# ADR 0002: Use an async, selectively typed API-Football client

## Status

Accepted on 2026-08-19.

## Context

The Milestone 1 probe exposed the upstream envelope, header authentication,
quota counters, and API-level errors inside successful HTTP responses. The
production boundary now needs reusable connection management, runtime response
validation, safe failures, and deterministic tests without modeling API-
Football's entire surface.

## Decision

- Use one scoped `httpx.AsyncClient` owned by `ApiFootballClient`.
- Keep authentication, base URL, timeout, HTTP behavior, and upstream parsing
  inside that client boundary.
- Use Pydantic request models with extra fields forbidden.
- Model only upstream response fields used by the application, require their
  expected types, and ignore unrelated extra response fields.
- Begin with countries and the `country` plus `season` leagues query only.
- Inject the HTTP transport and clock for deterministic offline tests.
- Expose small, secret-safe client exceptions instead of raw `httpx` or
  Pydantic exceptions.
- Capture per-response quota and retrieval metadata. Defer caching, persistent
  quota state, retries, and the complete normalized error taxonomy to
  Milestone 3.

## Alternatives considered

- A synchronous client would be simpler at this moment but would require an
  adapter or later conversion for async MCP and orchestration boundaries.
- Dataclasses or `TypedDict` would avoid Pydantic, but neither validates
  untrusted JSON at runtime without substantial manual parsing code.
- Strictly modeling every upstream field would detect more drift but create a
  large, brittle surface for fields the application does not use.
- A generic endpoint registry would reduce repetition later but is speculative
  before multiple workflows demonstrate a real need.

## Consequences

- Callers use `async` and must close the client, preferably with `async with`.
- Pydantic becomes a runtime dependency.
- Unexpected changes to required fields fail at the API-client boundary, while
  unrelated upstream additions remain compatible.
- New resources require explicit request models, response models, client
  methods, and tests.
- The implementation remains intentionally incomplete until later milestones
  add cache, retry, MCP, orchestration, and presentation boundaries.
