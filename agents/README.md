# Agents Runner

Use `spanish_workflow.py` to spin up Codex-driven specialists via the Agents SDK.

## Prerequisites
- Python 3.11+ with the `agents` SDK available (`pip install openai-agents`).
- Codex CLI (`npm install -g @openai/codex-cli`).
- `OPENAI_API_KEY` exported in your shell. Run `export OPENAI_API_KEY=sk-…` or place it in your environment manager.

## Launch
```bash
python agents/spanish_workflow.py
```

The script starts Codex CLI as an MCP server and hands control to a Workflow Lead agent. Expect new artifacts in `kg/`, `state/`, `lesson_templates/`, `evaluation/`, `tests/`, and `mcp_servers/`. Results and remaining work land in `STATUS.md`.
