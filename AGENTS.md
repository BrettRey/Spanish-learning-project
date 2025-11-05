# Repository Guidelines

## Project Structure & Module Organization
Keep high-level product notes in `idea.md`. When implementing the coach stack, mirror the layout sketched there so agents can navigate consistently:
- `mcp_servers/` holds MCP adapters (`kg_server.py`, `srs_server.py`, `speech_server.py`). Give each server its own package with a `__main__.py` that exposes a `--help` flag.
- `state/` stores learner-facing YAML configs and SQLite mastery data; track schema files, but never commit personal learner exports.
- `kg/` contains seed graph YAML/JSON in `seed/` and the compiled `kg.sqlite`.
- `lesson_templates/`, `evaluation/`, and optional `ui/` host prompts, rubrics, and front-end assets. Shared helpers belong in `lib/`.

## Build, Test, and Development Commands
Use Python 3.11+ and isolate dependencies: `python -m venv .venv && source .venv/bin/activate`. Install tooling with `pip install -r requirements.txt` (generate it via `pip freeze > requirements.txt` once dependencies settle). Key workflows:
- `make dev` (or `uv run python -m mcp_servers.kg_server`) to launch individual MCP services locally.
- `pytest` to run unit tests; add `--maxfail=1 --disable-warnings` for quick feedback.
- `ruff check .` and `ruff format .` keep style consistent; hook them into `pre-commit` if possible.

## Coding Style & Naming Conventions
Favor typed, documented Python modules. Follow PEP 8 with 4-space indentation, `snake_case` for functions/modules, and `UpperCamelCase` for classes. Keep server entry points in `main()` functions for easy invocation. Configuration files use lower-case kebab names (`lesson_templates/conversation-a2.yaml`). Prefer explicit imports over `from module import *`.

## Testing Guidelines
Place tests under `tests/` mirroring source structure (e.g., `mcp_servers/tests/test_kg_server.py`). Use `pytest` parametrization for graph/SRS scenarios and create fixtures for temporary SQLite databases. Aim for coverage on all tool endpoints and edge-case scheduling logic; document gaps in `tests/README.md`.

## Commit & Pull Request Guidelines
Adopt Conventional Commits (`feat:`, `fix:`, `chore:`) so downstream automation can generate release notes. Each PR should link the relevant Trello/GitHub issue, summarize behavioral impact, list new commands or configs, and include screenshots or transcripts when UX changes affect lessons. Mention test commands you ran (`pytest`, `ruff`) in the PR checklist.

## Security & Configuration Tips
Never commit learner-identifiable data or API keys. Use `.env` for runtime secrets and reference them via `os.environ`. When sharing demo state, sanitize names and reset review histories. Rotate Whisper or OpenAI keys regularly and document the rotation process in a private runbook.
