# Documentation Index

This directory contains comprehensive documentation for the Spanish Learning Project.

## 📖 Core Documentation

### Project Overview
- [**IMPLEMENTATION_SUMMARY.md**](../IMPLEMENTATION_SUMMARY.md) - Complete build summary with technical details
- [**STRATEGY.md**](../STRATEGY.md) - Strategic thinking, architectural decisions, and experimental directions
- [**STATUS.md**](../STATUS.md) - Implementation progress log with timeline

### Product Documentation
- [**idea.md**](../idea.md) - High-level product vision and architectural sketch
- [**README.md**](../README.md) - Main project README with quick start guides

### Development
- [**CHANGELOG.md**](../CHANGELOG.md) - Version history with features and fixes
- [**TODO.md**](../TODO.md) - Current priorities and roadmap
- [**DATA_SOURCES.md**](../DATA_SOURCES.md) - Corpus sources, licenses, and usage constraints

### AI Agent Guidelines
- [**CLAUDE.md**](../CLAUDE.md) - Guidelines for Claude Code when working with this repository
- [**AGENTS.md**](../AGENTS.md) - Repository guidelines (written for OpenAI agents)
- [**GEMINI.md**](../GEMINI.md) - Guidelines for Gemini (alternative AI agent)

## 📁 Subdirectories

### [handoffs/](handoffs/)
Session handoff documents from major development milestones. Each handoff includes:
- What was built
- Testing status and validation results
- Design decisions and rationale
- Prioritized next steps

**Latest**: [SESSION_HANDOFF_2025-11-06.md](handoffs/SESSION_HANDOFF_2025-11-06.md) - Prerequisite-aware curriculum complete

### [sessions/](sessions/)
Real language learning session transcripts and analysis. Used for:
- Identifying UX friction points
- Validating pedagogical approach
- Testing strand balance
- Improving coaching instructions

**Latest**: [analysis-20251106.md](sessions/analysis-20251106.md) - First real session analysis with comprehensive findings

## 🏗️ Architecture

### High-Level Architecture

```
┌─────────────┐
│  LLM Coach  │  Conversational teaching, quality assessment
└──────┬──────┘
       │ Uses atomic tools
       ▼
┌─────────────────────────────────────────┐
│      Atomic Coaching Tools              │
│  preview, adjust, start, record, end    │
└──┬──────────────────────────────────┬───┘
   │                                  │
   ▼                                  ▼
┌────────────┐                  ┌────────────┐
│    KG      │                  │    SRS     │
│  (nodes,   │                  │  (FSRS,    │
│   edges)   │                  │  mastery)  │
└────────────┘                  └────────────┘
```

### Key Components

1. **Knowledge Graph (KG)** - [kg/README.md](../kg/README.md)
   - YAML → SQLite build system
   - 100+ B1 nodes with prerequisites
   - CEFR alignment and frequency data

2. **Spaced Repetition System (SRS)** - [state/README.md](../state/README.md)
   - Full FSRS algorithm
   - Per-learner mastery tracking
   - Four Strands session planning

3. **MCP Servers** - [mcp_servers/*/README.md](../mcp_servers/)
   - KG Server: `kg.next()`, `kg.prompt()`, `kg.add_evidence()`
   - SRS Server: `srs.due()`, `srs.update()`, `srs.stats()`
   - Speech Server: `speech.recognize_from_mic()`, `speech.synthesize_to_file()`

## 🎓 Pedagogical Framework

### Four Strands (Nation)
- **Meaning-focused Input** (25%): Comprehension activities
- **Meaning-focused Output** (25%): Communication activities
- **Language-focused Learning** (25%): Explicit study
- **Fluency Development** (25%): Automaticity practice with mastered content (i-1)

### Correction Philosophy
- **Meaning before form** - Always acknowledge meaning first
- **1-2 corrections maximum** per utterance (varies by strand)
- **Implicit recasts preferred** - Model correctly without "that's wrong"
- **Explicit corrections** - Only for repeated errors or in language-focused strand

### i-1 Principle
Fluency practice uses material below current proficiency level:
- Learner profile tracks skill-specific CEFR levels (reading, listening, speaking, writing)
- Each skill has `current_level` (working now) and `secure_level` (i-1, ready for fluency)
- Auto-promotion when 80% of next CEFR level is mastered

## 🔬 Research & Data

### Frequency Data
- **SUBTLEX-ESP**: Subtitle corpus frequencies
- **Multilex**: Word family frequencies
- **GPT Familiarity/Affect**: AI-estimated familiarity, valence, arousal, concreteness
- **Corpus del Español**: Davies corpus frequencies

All lemmas include Zipf scores (log10 frequency per billion words, 1-7 scale).

### PRESEEA Corpus
Oral Spanish transcripts from 15+ cities with speaker metadata. Used for:
- Authentic example sentences in KG nodes
- Natural language sampling for exercise generation
- Frequency validation against conversational data

### CEFR Alignment
All content mapped to Common European Framework of Reference levels (A1-B1 currently).

## 🧪 Testing

**Test Coverage**: 70% minimum (configured in pyproject.toml)

**Test Categories** (pytest markers):
- `unit`: Unit tests (no external resources)
- `integration`: Integration tests (use databases/files)
- `slow`: Tests taking >1 second
- `kg`, `srs`, `mcp`, `fsrs`: Component-specific

**Run tests**:
```bash
pytest                    # All tests
pytest -m unit            # Unit tests only
pytest -m "kg and not slow"  # Fast KG tests
make test                 # Via Makefile
```

## 🔧 Development Workflow

1. **Setup**: `python3.11 -m venv .venv && pip install -e .`
2. **Build KG**: `python kg/build.py kg/seed kg.sqlite`
3. **Run tests**: `pytest` or `make test`
4. **Format code**: `ruff format .`
5. **Lint**: `ruff check .`

See [README.md](../README.md#for-developers-three-commands-to-first-result) for detailed setup instructions.

## 📊 Metrics & Analysis

### Session Metrics
- Exercises completed
- Quality distribution (0-5 scale)
- Strand balance (actual vs. target 25%)
- FSRS parameters (stability, difficulty)
- Mastery status transitions

### Learner Progress
- Total sessions
- Current streak
- Items by mastery status (new, learning, mastered)
- Skill-specific CEFR levels
- Common error patterns

## 🤝 Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) (if you want to create this file) for:
- Code style conventions
- Testing requirements
- PR guidelines
- How to add new KG nodes safely

## 📜 License & Ethics

- **Code**: [Add license here]
- **Content**: See [DATA_SOURCES.md](../DATA_SOURCES.md) for corpus licenses
- **Privacy**: Never commit learner-identifiable data or API keys

---

**For questions or feedback**: [GitHub Issues](https://github.com/BrettRey/Spanish-learning-project/issues)

**Last updated**: 2025-11-06
