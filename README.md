# Football Intelligence Copilot

A learning-first project for building a local football assistant with a curated
MCP server, a local tool-calling model, LangGraph, and Streamlit.

The project is currently at **Milestone 2: build a typed Python API client**.
The Milestone 1 probe remains as an executable learning artifact. There is
deliberately no cache, MCP, LLM, LangGraph, or UI code yet.

## Milestone 1 setup

1. Open `.env` and enter the API key from API-Football's **Account → My Access**:

   ```dotenv
   API_FOOTBALL_KEY=your-key-here
   ```

2. Install the pinned project environment:

   ```bash
   uv sync --group dev
   ```

3. Make the smallest request:

   ```bash
   uv run football-api-probe countries
   ```

4. Explore parameterized endpoints:

   ```bash
   uv run football-api-probe leagues --param country=England --param season=2025
   uv run football-api-probe standings --param league=39 --param season=2025
   ```

The probe prints the endpoint, safe parameters, response envelope, and quota
headers. It never prints the API key. Each successful command consumes one API
request unless the upstream service handles it otherwise.

## Milestone 2 typed client

The production-facing boundary is an asynchronous `ApiFootballClient` with:

- secret-safe configuration loaded from `.env` or an injected mapping;
- strict typed arguments for the currently supported league query;
- selectively modeled Pydantic responses for countries and leagues;
- quota and UTC retrieval metadata on successful responses;
- safe configuration, transport, HTTP, API-level, and schema failures; and
- injectable HTTP transport and clock dependencies for deterministic tests.

Only `get_countries()` and `get_leagues(LeaguesQuery(...))` are supported. New
resources will be added only when an agreed workflow requires them.

```python
from football_copilot.api_football import (
    ApiFootballClient,
    LeaguesQuery,
    load_api_football_config,
)


async def load_english_leagues():
    config = load_api_football_config()
    async with ApiFootballClient(config) as client:
        return await client.get_leagues(
            LeaguesQuery(country="England", season=2024)
        )
```

## Development checks

These checks are offline and do not consume API quota:

```bash
uv run pytest
uv run ruff check .
```

## Milestone boundary

Milestone 2 is complete when we can explain and verify:

- Why configuration, transport, validation, and domain models are separate.
- Why the client is async and owns one scoped `httpx.AsyncClient`.
- Why request models reject extras while response models ignore unused extras.
- How HTTP, API-level, and schema failures cross the boundary safely.
- How mocked transports test requests without consuming live quota.
