# Football Intelligence Copilot

A learning-first project for building a local football assistant with a curated
MCP server, a local tool-calling model, LangGraph, and Streamlit.

The project is currently at **Milestone 1: understand API-Football directly**.
There is deliberately no MCP, LLM, LangGraph, or UI code yet.

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

## Development checks

These checks are offline and do not consume API quota:

```bash
uv run pytest
uv run ruff check .
```

## Milestone boundary

Milestone 1 is complete when we can explain:

- How the API key is transmitted.
- How query parameters are serialized.
- What `errors`, `results`, `paging`, and `response` mean.
- Which headers report daily and per-minute quota.
- How an HTTP error differs from an API-level error in an HTTP 200 response.

