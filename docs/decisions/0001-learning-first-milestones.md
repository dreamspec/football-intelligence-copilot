# ADR 0001: Build in executable learning milestones

## Status

Accepted

## Decision

Build one vertical milestone at a time. Each milestone must be executable,
tested, documented, and understood before later abstractions are added.

Milestone 1 will interact with API-Football directly. The typed client, cache,
MCP server, local model, LangGraph workflow, and UI will be introduced in later
milestones.

## Consequences

- The raw API contract is learned before it is hidden by framework code.
- Commits and documentation tell a clear engineering story.
- Some early probe code may be replaced rather than promoted into production.

