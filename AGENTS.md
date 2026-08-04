# Repository Guidelines

## Project Structure & Module Organization

This is a Python 3.13 project for an AI news workflow. Runtime code lives in `src/`. The main LangGraph pipeline is in `src/main.py`, with graph nodes in `src/nodes/`, agent setup in `src/agents/`, Tavily tooling in `src/agents/tools/`, and prompt builders in `src/prompts/`. Keep generated artifacts such as `__pycache__/` out of commits. There is no test suite yet; add tests under `tests/` when introducing behavior that can be validated without live API calls.

## Build, Test, and Development Commands

- `uv sync`: install dependencies from `pyproject.toml` and `uv.lock`.
- `uv run python -m src.main`: run the full newsletter graph: research, format, then send email.
- `uv run python -m src.agents.agent_pesquisador`: run the research agent interactively.
- `uv run pytest`: run tests once a `tests/` directory is added.

The project depends on external services. Copy `.env-example` to `.env` and set keys before running locally. Required services include Google Gemini (`GOOGLE_API_KEY`), Tavily (`TAVILY_API_KEY`), and Resend (`RESEND_API_KEY`, used by `node_send_email.py`).

## Coding Style & Naming Conventions

Use standard Python style with 4-space indentation, type hints for public functions, and concise module-level constants for environment defaults. Existing modules use Portuguese names and domain terms, such as `node_pesquisador`, `agent_formatador`, and `search_new`; follow that naming pattern for new workflow pieces. Keep node functions small and return `MessagesState`-compatible dictionaries. Prefer explicit imports from `src.*` packages.

No formatter or linter is configured yet. If adding one, update this guide and keep formatting changes separate from behavioral changes.

## Testing Guidelines

Use `pytest` for new tests. Name files `tests/test_<module>.py` and tests `test_<behavior>()`. Mock Gemini, Tavily, and Resend calls so tests do not require network access or real credentials. Focus coverage on prompt selection, response parsing, date-window handling, and graph node outputs.

## Scope Control

When the user asks for specific items such as `x` and `y`, execute only `x` and `y`. If an additional change like `z` seems useful but was not requested, do not implement it automatically. Finish the requested work first, then suggest `z` in the final response and ask whether the user wants it before making any extra changes. This applies especially to adding tests, refactors, polish, or auxiliary tooling that goes beyond the explicit request.

## Commit & Pull Request Guidelines

Recent history mostly uses short imperative messages, often Conventional Commit style, for example `feat: adiciona nó de envio de email e integra ao fluxo principal`. Prefer `feat:`, `fix:`, `refactor:`, or `test:` prefixes and keep the summary specific.

For pull requests, include the purpose, key files changed, test commands run, and any required environment variables. Add screenshots or rendered email samples when changing newsletter formatting.

## Security & Configuration Tips

Never commit `.env` or API keys. Keep recipient addresses, sender configuration, model names, and search limits configurable through environment variables when practical. Avoid logging full raw search responses if they may include sensitive content.

## Cursor Cloud specific instructions

- Toolchain: `uv` manages both Python 3.13 and dependencies. The startup update script runs `uv sync`, which provisions the pinned Python (`.python-version` = 3.13.9) and installs the locked deps into `.venv`. `uv` lives in `~/.local/bin`; if `uv: command not found`, add that to `PATH`. Run everything via `uv run ...`.
- Credentials are validated at import time, not just at call time. Importing `src.main` (or building the graph) transitively imports the agents: with `PROVIDER_LLM=google` (the default), `src/llm.py` raises if `GOOGLE_API_KEY` is unset, and `src/agents/tools/search_tool.py` instantiates `TavilyClient` at module load, so `TAVILY_API_KEY` must be set even to import the search node or compile the full graph. To inspect/compile the graph without a Google key, use `PROVIDER_LLM=ollama` (the Ollama provider is not validated at import); a `TAVILY_API_KEY` value (even a dummy) is still required to import the search tool.
- Running `uv run python -m src.main` performs a live Tavily news search, a real LLM synthesis, and sends an actual email via Resend. It needs `TAVILY_API_KEY`, `RESEND_API_KEY`, an LLM (`GOOGLE_API_KEY` or a reachable Ollama via `OLLAMA_BASE_URL`), plus `NEWSLETTER_FROM_EMAIL` and `NEWSLETTER_TO_EMAIL`. Configure via `.env` (copy from `.env-example`); env vars injected by the platform also work since the code only calls `load_dotenv()` to augment them.
- No linter and no test suite are configured yet: `uv run pytest` fails because `pytest` is not installed and there is no `tests/` directory. Add tests under `tests/` with mocked Gemini/Tavily/Resend before relying on `uv run pytest`.
- Pure logic (URL safety in `src/security.py`, date parsing/sanitization in `src/agents/tools/search_tool.py`) can be exercised offline without live API calls once a `TAVILY_API_KEY` value is present for import.
