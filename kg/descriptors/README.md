# Descriptor Specification

This directory holds the CEFR-aligned descriptor tables that drive automated
generation of knowledge-graph nodes, lesson templates, and evaluation rubrics.

## File Format

Descriptors live in UTF-8 CSV files. Each row describes a single outcome and
references the supporting linguistic assets required to fulfil it. The canonical
column set is:

| Column | Description |
| --- | --- |
| `descriptor_id` | Unique identifier in the form `cando.es.<slug>` |
| `cefr_level` | CEFR band (A1…C2) |
| `category` | Skill domain (Spoken Production, Interaction, Mediation, etc.) |
| `descriptor_text` | Human-readable descriptor (CEFR/PCIC phrasing) |
| `priority` | `core`, `supporting`, or `extension` for roadmap planning |
| `prerequisite_nodes` | Semicolon-separated list of KG node IDs that must exist first |
| `target_functions` | Communicative functions to emphasise |
| `target_constructions` | Key grammatical constructions (existing or planned) |
| `lexemes_required` | High-frequency lexical families (Zipf ≥ threshold) |
| `pragmatics` | Pragmatic cues/discourse moves the learner must control |
| `evaluation_criteria` | Rubric IDs (e.g., `assessment.es.lexical_range_B1`) |
| `frequency_focus` | Notes on frequency bands / coverage expectations |
| `corpus_filters` | Hints for the sampler (subcorpus, speaker profile, regex) |
| `lesson_hooks` | Suggested task archetypes (role-play, monologue, mediation) |
| `notes` | Extra context, risks, or open questions |

### Conventions

- Use existing KG IDs when possible; list new IDs in `notes` so they can be
  scaffolded ahead of time.
- Keep `lexemes_required` ordered by descending frequency (pull from
  `frequency_lookup.py` or the SQLite index).
- `corpus_filters` should be machine-friendly hints, e.g.
  `subcorpus=Barcelona;speaker=I;regex="en mi opinión"`.
- When adapting descriptors from CEFR/PCIC, quote the source verbatim and add
  the citation in `notes`.

## Workflow

1. Append new descriptors to the relevant CSV (e.g., `b1_descriptors.csv`).
2. Run validation (planned script) to ensure IDs are unique and referenced nodes
   exist.
3. Use the descriptor rows as inputs to generators that produce YAML stubs,
   lesson templates, and rubric updates.
4. Review generated artifacts manually, confirm frequency bands, then import into
   `kg/seed`.

## TODO

- [ ] Add validator to cross-check descriptor prerequisites against `kg/seed`.
- [ ] Hook descriptor CSVs into KG auto-generation scripts.
