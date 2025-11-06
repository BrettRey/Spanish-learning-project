# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### To Do
See `SESSION_HANDOFF.md` for planned next steps:
- Migration runner with automatic backups
- Integration tests for session flow
- Configurable skill mapping (YAML)
- Frontier explainability (why included/excluded)
- Session analytics (correlate preferences with outcomes)

## [0.3.0] - 2025-11-06

### Added
- **Prerequisite-aware frontier filtering** (`get_frontier_nodes()` in `state/session_planner.py`)
  - Progressive curriculum selection based on KG prerequisites
  - Only introduces content when all dependencies are satisfied
  - Completes the curriculum intelligence system
- **Skill-specific proficiency tracking** with i-1 fluency filtering
  - Per-skill CEFR levels (reading, listening, speaking, writing) in `learner.yaml`
  - `current_level` (working level) vs `secure_level` (i-1, ready for fluency)
  - `get_fluency_candidates()` filters by mastery + skill + CEFR ≤ secure_level
  - Implements Nation's principle: fluency uses material below proficiency
- **Auto-promotion logic** (`update_secure_levels()` in `coach.py`)
  - Automatically promotes secure_level when 80% of next CEFR level mastered
  - Updates `learner.yaml` automatically
- **Session plan caching** (5-minute TTL)
  - Prevents plan drift between preview and start
  - Cache stored in `mastery.sqlite` with automatic invalidation
- **Audit trail for learner agency**
  - `negotiated_weights` and `approved_plan` columns in `session_log`
  - JSON logging of learner preferences and session structure
  - Enables analysis of preference correlation with outcomes
- **CI/CD pipeline** (`.github/workflows/ci.yml`)
  - Matrix testing (Python 3.11, 3.12)
  - Ruff linting → KG build → mastery DB init → pytest with coverage
  - Runs on push to `main`/`claude/**` branches and PRs to `main`
- **Knowledge Graph visualization** (`scripts/viz_kg.py`)
  - Interactive HTML with zoom/pan/drag
  - Static PNG with edge labels
  - Filtering by node type, CEFR level, or neighborhood
  - Multiple layouts: force-directed, hierarchical, CEFR-layered
- **LLanguageMe launcher** (interactive CLI)
  - First-time onboarding (2-minute setup)
  - Generates `.session_context.md` with coaching instructions
  - Solves cold-start problem for new learners

### Changed
- **Weight normalization** in `adjust_focus()`
  - Bounds weights to [0, 2.0] and normalizes sum to 4.0
  - Ensures predictable session planning across all goals
- **Four Strands balancing** with progressive pressure algorithm
  - Scarcity-aware handling when not enough content
  - Improved strand distribution convergence
- **Session planner** refactored for atomic operations
  - `preview_session()`, `start_session()`, `record_exercise()`, `end_session()`
  - Transactional guarantees for coach API

### Fixed
- Schema mismatches between `schema.sql` and `coach.py` (commit ea5c9e0)
- Ruff linting errors in `coach.py` and `session_planner.py`

### Database Migrations
- **Migration 003**: Skill proficiency tracking
  - Added `skill TEXT` column to `items` table
  - Created indexes: `idx_items_skill`, `idx_items_skill_mastery`
  - Updated `fluency_ready_items` view with skill awareness
- **Migration 004**: Session audit trail
  - Added `negotiated_weights TEXT`, `approved_plan TEXT` to `session_log`
  - JSON logging for learner agency analysis

### Testing
- 101/101 tests passing
- End-to-end session flow validated
- Frontier filtering verified with real KG data
- Skill backfill: 92.6% coverage (100/108 items)

## [0.2.0] - 2025-11-04

### Added
- **Learner agency tracking** (`session_log` table)
  - Records learner preferences and session outcomes
  - Foundation for preference-outcome correlation analysis
- **B1 content expansion** (40+ new KG nodes)
  - CanDo descriptors from PCIC
  - Functions, Constructions, Lexemes with CEFR alignment
  - Discourse moves and pragmatic cues
  - Topics with authentic examples
  - Assessment criteria for speaking/writing
- **Frequency data integration**
  - Normalized SUBTLEX, Multilex, GPT familiarity/affect, Corpus del Español
  - `data/frequency/frequency.sqlite` with Zipf scores
  - `tools/frequency_lookup.py` for quick lookups
- **PRESEEA corpus processing**
  - `scripts/process_preseea.py` extracts speaker metadata and turns
  - `tools/preseea_sampler.py` for targeted sampling
  - `corpus_examples` field in KG nodes with transcript citations
- **Descriptor schema** (`kg/descriptors/`)
  - B1 descriptors with prerequisites and frequency targets
  - Foundation for automated KG generation
- **Narrative module** (B1 storytelling)
  - Lesson template: `lesson_templates/narrate-past-events-b1.yaml`
  - Assessment rubric: `evaluation/narrative-speaking-b1.yaml`
  - Linked to `cando.es.narrate_past_events_B1`

### Changed
- Bootstrap items now assign skills via `infer_skill()` function
- Session planner hygiene improvements
- Code quality improvements (ruff formatting)

### Database Migrations
- Initial `session_log` table for learner agency tracking

## [0.1.0] - 2025-11-04

### Added - Foundation Complete
Built by 6 parallel Claude Code agents. Core architecture established.

#### 1. Knowledge Graph System (`kg/`)
- Build script compiles YAML → SQLite (`kg/build.py`)
- 10 Spanish language nodes (A1-B1)
- 31 relationship edges (prerequisite_of, realizes, contrasts_with, etc.)
- Node types: Lexeme, Construction, Morph, Function, CanDo, Topic, Script, PhonologyItem
- Validation script (`scripts/validate_kg.py`)

#### 2. Spaced Repetition System (`state/`)
- Full FSRS algorithm implementation (`state/fsrs.py`)
- SQLite schema with review history (`state/schema.sql`)
- Database initialization utilities (`state/db_init.py`)
- Example learner profile (`state/learner.yaml`)
- Four Strands session planning (`state/session_planner.py`)
- Atomic coaching tools (`state/coach.py`)

#### 3. MCP Servers (`mcp_servers/`)
- **KG Server**: 3 tools (`kg.next`, `kg.prompt`, `kg.add_evidence`)
- **SRS Server**: 3 tools (`srs.due`, `srs.update`, `srs.stats`)
- **Speech Server**: 2 tools (`speech.recognize_from_mic`, `speech.synthesize_to_file`)
- All servers with test/interactive/mock modes
- Production-ready structure with README documentation

#### 4. Lesson Templates & Rubrics (`lesson_templates/`, `evaluation/`)
- 5 lesson templates (conversation, grammar, vocabulary, listening, integrated)
- 3 CEFR-aligned rubrics (speaking, writing, can-do mapping)
- 12-point scale for A2-B1
- Research-based pedagogy

#### 5. Testing Infrastructure (`tests/`)
- 65 initial tests across 4 test files
- Pytest configuration with coverage targets
- 14+ reusable fixtures
- Test markers: unit, integration, slow, kg, srs, mcp, fsrs

#### 6. Speech Processing
- Real-time speech recognition using `SpeechRecognition`
- Text-to-speech synthesis using `pyttsx3`
- Integration with MCP server architecture

### Technical Stats (v0.1.0)
- 12,900+ lines of code
- 52 files created
- All systems verified working
- Foundation for progressive language learning

## [0.0.1] - 2025-02-14

### Added
- Initial project setup (OpenAI Codex approach - deprecated)
- `agents/spanish_workflow.py` multi-agent runner
- Virtual environment configuration for M4 Mac

### Note
This approach was replaced with Claude Code parallel agents on 2025-11-04.

---

## Version History Summary

- **v0.3.0** (2025-11-06): Production-ready with prerequisite-aware curriculum, skill tracking, CI/CD
- **v0.2.0** (2025-11-04): B1 expansion, frequency data, learner agency tracking
- **v0.1.0** (2025-11-04): Foundation complete (KG + SRS + MCP + testing)
- **v0.0.1** (2025-02-14): Initial prototype (deprecated)

[Unreleased]: https://github.com/BrettRey/Spanish-learning-project/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/BrettRey/Spanish-learning-project/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/BrettRey/Spanish-learning-project/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/BrettRey/Spanish-learning-project/compare/v0.0.1...v0.1.0
[0.0.1]: https://github.com/BrettRey/Spanish-learning-project/releases/tag/v0.0.1
