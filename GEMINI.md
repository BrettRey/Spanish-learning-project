# Gemini Code Assistant Context

This document provides context for the Gemini code assistant to understand the Spanish Learning Coach project.

## Project Overview

This is a Python project for a Spanish learning coach. It uses a knowledge graph and a spaced repetition system (SRS) to help users learn Spanish.

The project is structured as follows:

*   `kg/`: Contains the knowledge graph, which is built from YAML files into a SQLite database.
*   `state/`: Contains the spaced repetition system (SRS) data, which is also stored in a SQLite database.
*   `mcp_servers/`: Contains the MCP (Multi-Component Platform) servers for the knowledge graph and SRS. These servers expose APIs for interacting with the KG and SRS.
*   `lesson_templates/`: Contains YAML files for different types of lessons.
*   `evaluation/`: Contains YAML files for evaluation rubrics.
*   `tests/`: Contains pytest tests for the project.

The system is designed to be modular, with separate components for the knowledge graph, SRS, lesson templates, and evaluation rubrics. The project is architected with a separation of concerns, where different components handle what to teach, when to review, how to teach, and how to assess.

## Building and Running

To build and run the project, follow these steps:

1.  Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

2.  Build the knowledge graph:

    ```bash
    python kg/build.py kg/seed kg.sqlite
    ```

3.  Run the tests:

    ```bash
    pytest
    ```

4.  Run the MCP servers:

    ```bash
    python -m mcp_servers.kg_server
    python -m mcp_servers.srs_server
    ```

## Development Conventions

*   **Linting and Formatting:** The project uses `ruff` for linting and formatting to enforce PEP 8 style guidelines.
*   **Testing:** The project uses `pytest` for testing, with a target of 70% code coverage.
*   **Commit Messages:** The project uses Conventional Commits for commit messages.
*   **Type Hints and Docstrings:** The project uses type hints and docstrings.
