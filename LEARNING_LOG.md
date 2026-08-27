# Learning log

## Milestone 1 — API-Football contract

Questions to answer after running the probe:

1. Why is the API key sent in a header rather than a query parameter?
2. What is the difference between the HTTP status and the `errors` field?
3. Why can `results` legitimately be zero?
4. What do the daily and per-minute remaining-request headers represent?
5. Which parts of the response should a future typed client preserve?

Record observations below without copying the API key.

### Observations

- On 2026-08-17, `GET /countries` succeeded with HTTP status `200`.
- The request used no query parameters and returned `171` results.
- The response contained no API-level errors: `errors` was an empty list.
- Pagination reported page `1` of `1`.
- The first sample record was Albania (`AL`) with a flag URL.
- The daily quota headers reported `100` allowed and `99` remaining.
- The per-minute headers reported `10` allowed and `9` remaining.
- The API key was sent only in the request header and was not included in the
  printable probe result.

### Parameterized request observations

- On 2026-08-19, `GET /leagues?country=England&season=2025` reached the API but
  returned an API-level plan error. The free plan reported access to seasons
  from 2022 through 2024, so endpoint availability cannot be assumed from
  documentation alone.
- `GET /leagues?country=England&season=2024` succeeded with HTTP status `200`,
  returned `44` results, and reported page `1` of `1`.
- The first result was Premier League ID `39`. API season `2024` represented the
  2024–25 season, from 2024-08-16 through 2025-05-25.
- Coverage was available for standings, injuries, lineups, and fixture/player
  statistics in the sampled league-season; odds coverage was `false`.
- The successful response reported `99` daily and `9` per-minute requests
  remaining. The probe did not expose quota headers from the preceding
  API-level error, so that failed request's quota cost could not be proven.

## Milestone 2 — Typed API client

- The production client is async because later MCP and LangGraph boundaries
  will also be async, and one scoped client can reuse HTTP connections.
- Pydantic validates untrusted responses at runtime. Request models reject
  unknown inputs; response models ignore unused upstream additions but require
  the fields the application uses.
- The first production slice models only countries and leagues. Adding every
  endpoint now would weaken the learning and maintenance boundaries.
- Mock transports exercise authentication, query serialization, response
  parsing, error handling, and client shutdown without live quota usage.
- Response-local quota metadata is preserved on API-level and HTTP errors.
  Persistent quota tracking, retries, error taxonomy, and caching remain
  Milestone 3 work.
