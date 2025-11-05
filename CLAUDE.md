# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Spanish language learning coach system built around three core technologies:
- **Knowledge Graph (KG)**: Tracks language constructs, their prerequisites, and learner progress through nodes and edges
- **Spaced Repetition System (SRS)**: Schedules reviews using the FSRS algorithm to optimize retention
- **MCP Servers**: Expose KG, SRS, and speech processing as tools that can be called during lessons

The coach delivers personalized language lessons by querying the knowledge graph for learnable content (prerequisites satisfied but not yet mastered), scheduling reviews based on mastery data, and providing targeted corrections aligned with SLA research.

## Architecture

### Core Components
- **Knowledge Graph**: SQLite database tracking linguistic items, their relationships, and learner evidence
- **Learner State**: Per-learner configurations (CEFR goals, correction preferences) and mastery history
- **Lesson Templates**: Reusable scaffolds for exercises aligned to specific KG nodes
- **Assessment Rubrics**: CEFR-aligned evaluation criteria for scoring learner output
- **MCP Tool Servers**: Python services exposing KG queries, SRS scheduling, and speech processing

### Directory Structure
- `mcp_servers/`: MCP server implementations (to be built)
  - `kg_server`: Exposes `kg.next()`, `kg.prompt()`, `kg.add_evidence()` for curriculum selection
  - `srs_server`: Exposes `srs.due()`, `srs.update()` for spaced repetition scheduling
  - `speech_server`: Exposes `asr.transcribe()`, `tts.speak()` for speech processing
  - Each server should be a package with `__init__.py` and `__main__.py` for standalone execution
- `state/`: Per-learner configurations and mastery databases
  - `learner.yaml`: CEFR goals, correction style, L1 preferences, topics of interest
  - `mastery.sqlite`: Item-level review history with FSRS stability/difficulty parameters
- `kg/`: Knowledge graph data
  - `seed/`: YAML/JSON source files defining nodes and edges
  - `kg.sqlite`: Compiled graph database (generated from seed files)
- `lesson_templates/`: Exercise scaffolds in YAML/Markdown format
  - Each template specifies CEFR level, skill focus, and required KG nodes
- `evaluation/`: Assessment rubrics and CEFR can-do mappings
- `tests/`: pytest suites mirroring source structure (e.g., `mcp_servers/tests/test_kg_server.py`)

### Knowledge Graph Model
**Node types**: `Lexeme`, `Construction`, `Morph`, `Function`, `CanDo`, `Topic`, `Script`, `PhonologyItem`

**Edge types**: `prerequisite_of`, `realizes`, `contrasts_with`, `depends_on`, `practice_with`, `addresses_error`

Each node contains:
- Diagnostics (form, function, usage constraints)
- Practice prompts
- CEFR alignment metadata
- Evidence counters (successful productions, errors)

**Example node** (from `idea.md`):
```yaml
id: constr.es.subjunctive_present
type: Construction
label: Present subjunctive
prerequisites: [constr.es.present_indicative, morph.es.subjunctive_endings]
can_do: [cando.es.express_doubt_B1, cando.es.express_desire_A2]
diagnostics:
  - form: "yo hable, tú hables, él/ella hable..."
  - function: "express doubt, desire, emotion, uncertainty"
prompts:
  - "Express doubt about the weather tomorrow"
  - "Say what you want your friend to do"
```

## Development Commands

### Environment Setup
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # Once dependencies are established
```

### Building the Knowledge Graph
```bash
# Compile seed YAML/JSON into kg.sqlite
python kg/build.py seed/ kg.sqlite
```

### Running MCP Servers
```bash
# Start individual servers for development/testing
python -m mcp_servers.kg_server
python -m mcp_servers.srs_server
python -m mcp_servers.speech_server

# Each server should support --help for usage
```

### Testing
```bash
# Run all tests
pytest

# Quick feedback mode (stop on first failure)
pytest --maxfail=1 --disable-warnings

# Run specific test file
pytest tests/test_kg_server.py

# Tests mirror source structure
```

### Linting and Formatting
```bash
ruff check .
ruff format .
```

## Key Conventions

### Coding Style
- Python 3.11+ with type hints
- PEP 8: 4-space indentation, `snake_case` functions/modules, `UpperCamelCase` classes
- Server entry points in `main()` functions
- Configuration files use lowercase kebab-case (`conversation-a2.yaml`)
- Explicit imports; avoid `from module import *`

### Lesson Session Flow (Conceptual)
The intended workflow for a language coaching session:

1. **Selection**: Query `kg.next(learner_id, k)` to identify frontier nodes (prerequisites satisfied, not yet mastered) and `srs.due(learner_id)` for review items
2. **Task Generation**: For each selected node, call `kg.prompt(node_id, kind)` to retrieve an exercise scaffold
3. **Interaction**: Learner produces output (text or speech); if speech, transcribe via `asr.transcribe()`
4. **Assessment**: Score output against rubric, generating quality rating (0-5)
5. **Update**: Call `srs.update(item_id, quality)` to adjust FSRS parameters
6. **Loop**: Continue until session time expires
7. **Summary**: Update `state/learner.yaml` with progress notes

### Correction Philosophy
- Meaning before form
- Only 1-2 targeted corrections per utterance
- Implicit recasts by default; explicit corrections only on repeated errors
- All exercise results logged to `state/mastery.sqlite`

### Security & Data Privacy
- Never commit learner-identifiable data or API keys
- Use `.env` for runtime secrets, reference via `os.environ`
- Sanitize demo state before sharing
- `state/` tracks schema files but not personal learner exports

### Commit Conventions
Use Conventional Commits format:
- `feat:` for new features
- `fix:` for bug fixes
- `chore:` for maintenance tasks

Each PR should link relevant issues, summarize behavioral impact, list new commands/configs, and mention test commands run.

## SRS Data Model
Each item in `mastery.sqlite` links to a KG node:
```json
{
  "item_id": "card.es.subjunctive_present.001",
  "node_id": "constr.es.subjunctive_present",
  "type": "production",
  "last_review": "2025-11-04T10:00Z",
  "stability": 2.4,
  "difficulty": 4.8,
  "reps": 3
}
```

Use FSRS algorithm for scheduling; parameters are per-item (stability, difficulty) with optional global learner optimization.

## Important Files
- `idea.md`: High-level product vision and architectural sketch (contains OpenAI-specific orchestration ideas that can be adapted)
- `AGENTS.md`: Repository guidelines and conventions (written for OpenAI agents but contains useful build/style guidance)
- `STATUS.md`: Implementation progress log
