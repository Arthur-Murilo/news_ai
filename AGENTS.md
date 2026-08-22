# Repository Guidelines

## Project Structure & Module Organization

This is a Python 3.13 project for an AI news workflow. Runtime code lives in `src/`. The main LangGraph pipeline is in `src/main.py`, with graph nodes in `src/nodes/`, agent setup in `src/agents/`, Tavily tooling in `src/agents/tools/`, and prompt builders in `src/prompts/`. Keep generated artifacts such as `__pycache__/` out of commits. Tests live in `tests/` and should stay free of live API calls. Mock Gemini, Tavily, and Resend.

## Build, Test, and Development Commands

- `uv sync`: install dependencies from `pyproject.toml` and `uv.lock`.
- `uv run python -m src.main`: run the full newsletter graph: research, format, then send email.
- `uv run python -m src.agents.agent_pesquisador`: run the research agent interactively.
- `uv sync --group dev && uv run pytest`: run the local test suite.

The project depends on external services. Copy `.env-example` to `.env` and set keys before running locally. Required services include Google Gemini (`GOOGLE_API_KEY`), Tavily (`TAVILY_API_KEY`), and Resend (`RESEND_API_KEY`, used by `node_send_email.py`).

## Coding Style & Naming Conventions

Use standard Python style with 4-space indentation, type hints for public functions, and concise module-level constants for environment defaults. Existing modules use Portuguese names and domain terms, such as `node_pesquisador`, `agent_formatador`, and `search_new`; follow that naming pattern for new workflow pieces. Keep node functions small and return `NewsletterState`-compatible dictionaries. Prefer explicit imports from `src.*` packages.

No formatter or linter is configured yet. If adding one, update this guide and keep formatting changes separate from behavioral changes.

## Testing Guidelines

Use `pytest` for new tests. Name files `tests/test_<module>.py` and tests `test_<behavior>()`. Mock Gemini, Tavily, and Resend calls so tests do not require network access or real credentials. Focus coverage on prompt selection, response parsing, date-window handling, sent-news memory, scheduler persistence, and graph routing.

## Scope Control

When the user asks for specific items such as `x` and `y`, execute only `x` and `y`. If an additional change like `z` seems useful but was not requested, do not implement it automatically. Finish the requested work first, then suggest `z` in the final response and ask whether the user wants it before making any extra changes. This applies especially to adding tests, refactors, polish, or auxiliary tooling that goes beyond the explicit request.

## Commit & Pull Request Guidelines

Recent history mostly uses short imperative messages, often Conventional Commit style, for example `feat: adiciona nó de envio de email e integra ao fluxo principal`. Prefer `feat:`, `fix:`, `refactor:`, or `test:` prefixes and keep the summary specific.

For pull requests, include the purpose, key files changed, test commands run, and any required environment variables. Add screenshots or rendered email samples when changing newsletter formatting.

## Security & Configuration Tips

Never commit `.env` or API keys. Keep recipient addresses, sender configuration, model names, and search limits configurable through environment variables when practical. Avoid logging full raw search responses if they may include sensitive content.
