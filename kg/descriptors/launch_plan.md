# Descriptor & Automation Launch Plan (B1 Phase I)

## Objective
Operationalize the descriptor-driven workflow for B1 Spanish: every descriptor stored in `b1_descriptors.csv` should generate the supporting KG nodes, lesson assets, and evaluation hooks with minimal manual effort while preserving authenticity and traceability.

## Key Milestones

1. **Descriptor Inventory (WIP)**
   - Finish cataloguing B1 descriptors (target: 40) using the agreed schema.
   - Add source citations and frequency targets for each row.

2. **Generation Tooling**
   - Script to produce:
     1. Descriptor YAML (`kg/descriptors/generated/…`)
     2. KG node stubs (`kg/descriptors/node_stubs/…`)
     3. Lesson template skeletons (TODO)
     4. Evaluation rubric updates (TODO)
   - Integrate PRESEEA sampling hints (`corpus_filters`) for automated example suggestions.

3. **Validation**
   - Extend `scripts/validate_kg.py` (or new validator) to:
     - Ensure every descriptor has matching node stub.
     - Check referenced prerequisites exist.
     - Flag missing frequency/corpus metadata.

4. **Seed Expansion**
   - For each descriptor:
     - Fill in node stub (`type`, `metadata`, `corpus_examples`, etc.).
     - Update or create supporting functions/lexemes/pragmatic nodes as needed.

5. **Lesson Template Integration**
   - Map `lesson_hooks` to actual template files in `lesson_templates/`.
   - Provide rubric references in `evaluation/` aligned with `evaluation_criteria`.

## Immediate To-Do (Next 1–2 work blocks)

| Task | Owner | Notes |
| --- | --- | --- |
| Normalize corpus filters (regex escaping) | | Current scripts emit `regex=\…\"`; clean to `regex=\\bpattern\\b`. |
| Populate outstanding metadata/frequency for legacy lexeme nodes | | Completed for A1–B1 core set; verify when new nodes added. |
| Implement descriptor → lesson template generator | | Use `lesson_hooks` to seed `lesson_templates/*.md`. |
| Add validation step for descriptor/node parity | | Update `validate_kg.py` or new script. |

## Risks & Considerations

- **Authenticity**: only reference corpora we hold locally (PRESEEA, SUBTLEX) or cite external datasets per licensing.
- **Duplication**: ensure newly generated nodes do not conflict with existing IDs.
- **Scalability**: design scripts so adding B2/C levels later only requires new CSV entries.

## Next Checkpoint
Prepare a review after the first “generate → stub → finalize” cycle for three descriptors (narration, service negotiation, small talk) to confirm workflow and adjust the schema/tooling before scaling.
