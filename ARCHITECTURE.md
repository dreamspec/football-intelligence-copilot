# Architecture

## Current milestone

Only the upstream API boundary exists:

```text
Command line
    ↓
Safe API probe
    ↓
httpx
    ↓
API-Football REST API
```

The probe is intentionally not the future production API client. Its purpose is
to expose the raw upstream contract before Milestone 2 introduces typed models
and reusable client abstractions.

## Planned boundaries

```text
Streamlit
    ↓
LangGraph
    ↓
MCP client
    ↓
Curated Football MCP server
    ↓
Typed client + cache + quota tracking
    ↓
API-Football
```

The API key will remain inside the API-client boundary. It must never be sent to
the local language model or returned through an MCP tool result.

