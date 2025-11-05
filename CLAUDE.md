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
- `mcp_servers/`: MCP server implementations (✅ built and working)
  - `kg_server/`: Exposes `kg.next()`, `kg.prompt()`, `kg.add_evidence()` for curriculum selection
  - `srs_server/`: Exposes `srs.due()`, `srs.update()`, `srs.stats()` for spaced repetition scheduling
  - `speech_server/`: Exposes `speech.recognize_from_mic()`, `speech.synthesize_to_file()` for speech processing
  - Each server is a package with `__init__.py`, `__main__.py`, `server.py`, and README
- `kg/`: Knowledge graph data and build system
  - `build.py`: Compiler script (YAML → SQLite)
  - `seed/`: YAML source files defining nodes and edges
  - `descriptors/`: CEFR/PCIC descriptor mappings for KG generation
  - `phase_I_landscape.md`: B1 expansion roadmap
  - `kg.sqlite`: Compiled graph database (generated from seed files)
- `state/`: Per-learner configurations and mastery databases
  - `learner.yaml`: CEFR goals, correction style, L1 preferences, topics of interest
  - `mastery.sqlite`: Item-level review history with FSRS stability/difficulty parameters
  - `fsrs.py`: Full FSRS algorithm implementation
  - `db_init.py`: Database initialization utilities
  - `schema.sql`: SQLite schema definition
- `data/frequency/`: Frequency data and corpus resources
  - `frequency.sqlite`: Normalized frequency database (Zipf scores, familiarity, affect)
  - `normalized/`: Processed frequency lists (SUBTLEX, Multilex, GPT, Corpus del Español)
  - `preseea/`: PRESEEA corpus transcripts and processed samples
- `tools/`: Command-line utilities for data exploration
  - `frequency_lookup.py`: Quick frequency/familiarity lookups for lemmas/forms
  - `preseea_sampler.py`: Sample natural turns from PRESEEA by metadata filters
- `scripts/`: Build and validation utilities
  - `validate_kg.py`: Check KG nodes for required metadata (sources, corpus examples, frequency)
  - `build_frequency_index.py`: Generate frequency.sqlite from source files
  - `process_preseea.py`: Extract and normalize PRESEEA transcript data
- `lesson_templates/`: Exercise scaffolds in YAML/Markdown format
- `evaluation/`: Assessment rubrics and CEFR can-do mappings
- `tests/`: pytest suites mirroring source structure with 65+ tests and 14+ fixtures
- `agents/`: OpenAI workflow orchestrator (legacy, not actively used)

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
pip install -r requirements.txt

# Required for KG building
pip install pyyaml
```

### Building the Knowledge Graph
```bash
# Compile seed YAML into kg.sqlite
python kg/build.py kg/seed kg.sqlite

# Validate KG nodes (checks for required metadata, sources, corpus examples)
python scripts/validate_kg.py
```

### Running MCP Servers
Each server supports multiple modes for development and testing:

```bash
# Test mode (demonstrates all tools with mock or real data)
python -m mcp_servers.kg_server --test
python -m mcp_servers.srs_server --test
python -m mcp_servers.speech_server --test

# Interactive mode (manual testing via CLI)
python -m mcp_servers.kg_server --interactive
python -m mcp_servers.srs_server --interactive

# Use real databases instead of mock data
python -m mcp_servers.kg_server --test --no-mock

# Get help on available options
python -m mcp_servers.kg_server --help
```

### Testing
```bash
# Run all tests
pytest

# Run tests by marker (unit, integration, slow, kg, srs, mcp, fsrs)
pytest -m unit
pytest -m integration
pytest -m "kg and not slow"

# Quick feedback mode (stop on first failure, no coverage)
pytest --maxfail=1 --disable-warnings --no-cov

# Run specific test file
pytest tests/test_kg_server.py
pytest tests/mcp_servers/test_srs_server.py

# Parallel execution for speed
pytest -n auto

# Generate coverage report
pytest --cov --cov-report=html
# View at htmlcov/index.html
```

### Database Inspection
```bash
# View KG nodes and edges
sqlite3 kg.sqlite "SELECT node_id, type, label, cefr_level FROM nodes;"
sqlite3 kg.sqlite "SELECT source_id, edge_type, target_id FROM edges LIMIT 10;"

# Check prerequisite chains
sqlite3 kg.sqlite "
  SELECT n.label, e.edge_type, n2.label
  FROM nodes n
  JOIN edges e ON n.node_id = e.source_id
  JOIN nodes n2 ON e.target_id = n2.node_id
  WHERE e.edge_type = 'prerequisite_of';"

# View SRS items and review history
sqlite3 state/mastery.sqlite "SELECT * FROM items LIMIT 5;"
sqlite3 state/mastery.sqlite "SELECT * FROM review_history ORDER BY review_time DESC LIMIT 10;"

# Query frequency data
sqlite3 data/frequency/frequency.sqlite "SELECT lemma, zipf, familiarity FROM lemmas WHERE lemma = 'hablar';"
```

### Frequency and Corpus Tools
```bash
# Look up frequency for a lemma
python tools/frequency_lookup.py hablar

# Sample PRESEEA turns by speaker criteria
python tools/preseea_sampler.py --city MEXI --age H11 --limit 5

# Rebuild frequency index from source files
python scripts/build_frequency_index.py

# Process PRESEEA transcripts
python scripts/process_preseea.py data/frequency/preseea data/frequency/preseea/processed
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

### Testing Conventions
- Tests mirror source structure: `tests/mcp_servers/test_kg_server.py` tests `mcp_servers/kg_server/server.py`
- Use pytest markers for test categorization:
  - `@pytest.mark.unit`: Unit tests (no external resources)
  - `@pytest.mark.integration`: Integration tests (use databases/files)
  - `@pytest.mark.slow`: Tests taking >1 second
  - `@pytest.mark.kg`, `@pytest.mark.srs`, `@pytest.mark.mcp`, `@pytest.mark.fsrs`: Component-specific
- Coverage target: 70% minimum (configured in pyproject.toml)
- Fixtures in `tests/conftest.py` provide reusable test data and temporary databases

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

## Frequency Data and Corpus Integration

The system integrates multiple frequency and psycholinguistic datasets to inform vocabulary selection and sequencing:

### Frequency Database (`data/frequency/frequency.sqlite`)
Consolidated frequency data from:
- **SUBTLEX-ESP**: Subtitle corpus frequencies
- **Multilex**: Word family frequencies
- **GPT Familiarity/Affect**: AI-estimated familiarity, valence, arousal, concreteness
- **Corpus del Español**: Davies corpus frequencies

Each lemma/form includes Zipf scores (log10 frequency per billion words, normalized 1-7 scale) for easy comparison.

### PRESEEA Corpus (`data/frequency/preseea/`)
Oral Spanish transcripts from 15+ cities with speaker metadata (age, education, socioeconomic status). Used for:
- Authentic example sentences in KG nodes (`corpus_examples` field with turn references)
- Natural language sampling for exercise generation
- Frequency validation against real conversational data

### Tools
- `frequency_lookup.py`: Quick terminal lookup of Zipf scores and familiarity ratings
- `preseea_sampler.py`: Sample authentic turns by speaker demographics for targeted examples

All Lexeme nodes should include `frequency` metadata (Zipf scores, source corpus). All communicative nodes should include `corpus_examples` with citations to PRESEEA or other corpora.

## Important Files

### Documentation
- `idea.md`: High-level product vision and architectural sketch
- `STATUS.md`: Implementation progress log with timeline
- `IMPLEMENTATION_SUMMARY.md`: Detailed build summary from initial implementation
- `AGENTS.md`: Repository guidelines (written for OpenAI agents)
- `GEMINI.md`: Guidelines for Gemini (alternative AI agent)
- `kg/README.md`: Knowledge graph build system documentation
- `kg/phase_I_landscape.md`: B1 expansion roadmap and descriptors
- `state/README.md`: SRS database schema and FSRS algorithm documentation
- `data/frequency/README.md`: Frequency data sources and normalization
- `mcp_servers/*/README.md`: Individual MCP server documentation

### Configuration
- `pyproject.toml`: Pytest, ruff, and coverage configuration
- `requirements.txt`: Python dependencies
- `state/learner.yaml`: Example learner profile
- `state/schema.sql`: SRS database schema

### Key Implementation Files
- `kg/build.py`: Knowledge graph compiler (YAML → SQLite)
- `state/fsrs.py`: Full FSRS algorithm implementation
- `mcp_servers/kg_server/server.py`: Knowledge graph MCP tools
- `mcp_servers/srs_server/server.py`: Spaced repetition MCP tools
- `mcp_servers/speech_server/server.py`: Speech processing MCP tools
- `scripts/validate_kg.py`: KG node validation (checks metadata, sources, examples)
