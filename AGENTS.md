# Learning-first development contract

Work on one agreed milestone at a time.

Before changing code, explain the objective, architecture, affected interfaces,
important alternatives, and acceptance tests. Recommend a default when a design
choice is required and make the reasoning explicit.

Keep changes small and reviewable. Separate domain logic, infrastructure, and
presentation. Add tests for important behavior. Never print, commit, or request
the user's real API key in chat.

After changing code, summarize the change, walk through the important files,
trace one request end to end, explain failure modes, show test evidence, and give
the user a short understanding checkpoint. Do not start the next milestone until
the user confirms the current milestone is understood.

