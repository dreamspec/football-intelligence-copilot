# Architecture

## Current milestone

Milestone 2 adds a reusable typed boundary while preserving the educational
Milestone 1 probe:

```text
Command line                     Application or future MCP server
    ↓                                        ↓
Safe API probe                      Typed request models
    ↓                                        ↓
httpx                              ApiFootballClient
    ↓                              ├── secret-safe configuration
API-Football REST API              ├── HTTP lifecycle and safe errors
                                   └── typed response validation
                                              ↓
                                      httpx.AsyncClient
                                              ↓
                                      API-Football REST API
```

The probe is intentionally not the future production API client. Its purpose is
to expose the raw upstream contract. Production-facing callers use the typed
client and receive a validated envelope with quota and retrieval metadata.

Request models are strict because the application controls their inputs.
Response models require the fields the application depends on but ignore
unknown upstream fields, allowing API-Football to add unrelated data without
breaking the client. Countries and leagues are the only modeled resources.

The client owns authentication and removes raw `httpx` and Pydantic exceptions
at its public boundary. It captures response-local quota metadata but does not
yet cache data, retry requests, or persist quota state; those belong to
Milestone 3.

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
