"""Agents SDK runner that orchestrates Codex-powered specialists for this repo."""
from __future__ import annotations

import asyncio
import os

from agents import Agent, Runner, set_default_openai_api
from agents.mcp import MCPServerStdio


def require_api_key(env_var: str = "OPENAI_API_KEY") -> str:
    """Return the API key or raise with a helpful message."""
    key = os.getenv(env_var)
    if not key:
        raise RuntimeError(
            f"{env_var} is not set. Export your OpenAI key before launching the workflow."
        )
    return key


async def main() -> None:
    """Spin up the Codex MCP server and coordinate the multi-agent workflow."""
    set_default_openai_api(require_api_key())

    async with MCPServerStdio(
        name="Codex CLI",
        params={
            "command": "npx",
            "args": ["-y", "codex", "mcp"],
        },
        client_session_timeout_seconds=3600,
    ) as codex_mcp_server:
        curriculum_agent = Agent(
            name="Curriculum Architect",
            instructions=(
                "You maintain the language knowledge graph and learner state scaffolding. "
                "When delegated work, create or update YAML/SQLite stubs under kg/ and state/ "
                "so the planner has concrete nodes, prerequisites, and learner profiles. "
                "Consult AGENTS.md for directory expectations and always explain how the changes "
                "support CEFR-aligned progression."
            ),
            model="gpt-4.1",
            mcp_servers=[codex_mcp_server],
        )

        lesson_agent = Agent(
            name="Lesson Designer",
            instructions=(
                "You craft reusable lesson prompts and rubrics. "
                "Produce Markdown or YAML assets under lesson_templates/ and evaluation/ that Codex can call. "
                "Each template must note the CEFR target, skill focus, and required MCP tools."
            ),
            model="gpt-4.1-mini",
            mcp_servers=[codex_mcp_server],
        )

        tooling_agent = Agent(
            name="Tooling Engineer",
            instructions=(
                "You implement Python MCP servers and shared helpers. "
                "Follow the structure in AGENTS.md: create packages within mcp_servers/ with __init__.py and "
                "__main__.py, document CLI usage, and ensure each exposed tool has docstrings and type hints. "
                "Prefer small, testable modules and stub external integrations where data is unavailable."
            ),
            model="gpt-4.1",
            mcp_servers=[codex_mcp_server],
        )

        qa_agent = Agent(
            name="Learning QA",
            instructions=(
                "You enforce testing and evaluation quality. "
                "Write pytest suites under tests/ that validate kg queries, scheduling logic, and template coverage. "
                "If code is not present yet, create red-green-ready stubs and list assumptions in TESTING_NOTES.md."
            ),
            model="gpt-4.1-mini",
            mcp_servers=[codex_mcp_server],
        )

        project_manager_agent = Agent(
            name="Workflow Lead",
            instructions=(
                "You coordinate specialists to build out the Spanish-learning project. "
                "Break the high-level goal into ordered tasks, hand each to the right agent, "
                "and block hand-offs on deliverable checks (files exist, lint, tests). "
                "After completion, compile a STATUS.md summary with open questions, test evidence, and next steps."
            ),
            model="gpt-4.1",
            mcp_servers=[codex_mcp_server],
        )

        project_manager_agent.handoffs = [
            curriculum_agent,
            lesson_agent,
            tooling_agent,
            qa_agent,
        ]
        curriculum_agent.handoffs = [project_manager_agent]
        lesson_agent.handoffs = [project_manager_agent]
        tooling_agent.handoffs = [project_manager_agent]
        qa_agent.handoffs = [project_manager_agent]

        task_list = """
Goal: Bootstrap the Spanish-language coaching workspace so agents can deliver tutor sessions end-to-end.

High-level requirements:
- Establish kg/, state/, lesson_templates/, evaluation/, tests/, and mcp_servers/ with meaningful starter files.
- Produce a CEFR-aligned roadmap for an A2 learner transitioning toward B1 conversation.
- Implement at least one MCP server stub (kg or srs) exposing list_nodes and update_mastery commands.
- Ship a minimal lesson template plus rubric ready for Codex-driven practice.
- Add automated checks or placeholders so future agents can extend safely.

Constraints:
- Follow the repository guidance in AGENTS.md and avoid committing learner-identifiable data.
- Keep outputs deterministic and small; prefer YAML and Markdown for specs.
- Report completion status and outstanding risks in STATUS.md before returning control.
"""

        result = await Runner.run(
            project_manager_agent,
            task_list,
            max_turns=40,
        )
        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
