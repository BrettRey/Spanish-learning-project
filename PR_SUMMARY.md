# PR Summary: `claude/review-pro-011CUrWFJbLAnq962RJQ3nae` → `main`

## Overview

This branch implements **ChatGPT's post-merge recommendations** plus **prerequisite-aware frontier filtering** to complete the core curriculum intelligence system.

## What's Been Shipped

### 1. Skill-Specific Proficiency Tracking (e7b476c)
- **Per-skill proficiency**: `reading`, `listening`, `speaking`, `writing` tracked separately
- **i-1 fluency filtering**: Fluency practice restricted to material at/below `secure_level`
- **Auto-promotion**: When 80% of next CEFR level mastered → promote `secure_level`
- **Migration 003**: Added `skill` column to `items` table with indexes
- **Files**: `state/learner.yaml`, `state/coach.py`, `state/session_planner.py`, `state/schema.sql`

### 2. Robustness Improvements (1434598)
- **GitHub Actions CI**: Matrix testing on Python 3.11/3.12, ruff linting, pytest + coverage
- **Strand scarcity pressure**: Re-normalize weights across viable strands only (sum=4.0)
- **Preview→start plan drift fix**: 5-minute TTL cache for approved plans
- **Session audit trail**: JSON `negotiated_weights` + `approved_plan` logged to `session_log`
- **Migration 004**: Added audit columns
- **Files**: `.github/workflows/ci.yml`, `state/coach.py`, `state/session_planner.py`, `state/migrations/004_session_audit_trail.sql`

### 3. Prerequisite-Aware Frontier Filtering (bfa89d1)
- **Full KG traversal**: Checks `prerequisite_of` edges for dependency satisfaction
- **Algorithm**:
  1. Query nodes at/below learner's current CEFR level
  2. Filter to unlearned nodes (status='new' or no item)
  3. Check all prerequisites satisfied (prereqs must have items with status != 'new')
  4. Infer `primary_strand` from node type
  5. Prioritize: no prereqs first, then lower CEFR, then alphabetical
- **Files**: `state/session_planner.py`

### 4. Additional Improvements
- **LLanguageMe launcher** (c751e18): Interactive onboarding + session context generation
- **KG visualization** (7c72899): Interactive HTML + static PNG exports with `scripts/viz_kg.py`
- **Weight normalization** (8cf5f66): Bound [0, 2.0], normalize to sum=4.0
- **Ruff auto-fixes** (9e3b7a5): Modernized type hints, organized imports

## Pre-Merge Checks ✅

All three required checks completed:

### 1. CI Configuration ✅
- Workflow file: `.github/workflows/ci.yml`
- Valid YAML syntax
- Tests ruff, KG build, DB init, pytest with coverage
- Ready to run on push (requires GitHub Actions enabled)

### 2. Migrations Smoke Test ✅
```
Migration 003 (skill column): ✓
  - Column added: skill TEXT
  - Indexes created: idx_items_skill, idx_items_skill_mastery
  - View updated: fluency_ready_items

Migration 004 (audit trail): ✓
  - Columns added: negotiated_weights TEXT, approved_plan TEXT
  - Audit trail logging verified in session flow
```

### 3. Skill Backfill ✅
```
Items with skills: 100/108 (92.6%)
  - 8 reading
  - 39 speaking
  - 53 writing
  - 8 NULL (test fixtures - acceptable)
```

## Testing Status

- **Unit tests**: 101/101 passing
- **Smoke tests**: Preview → start → record → end flow verified
- **Audit trail**: JSON logging confirmed in `session_log` table
- **Frontier filtering**: Tested with real KG data, prerequisite logic validated

## What This Enables

The system can now:
- ✅ Review existing progress (SRS due items)
- ✅ Practice mastered material (fluency with i-1 filtering)
- ✅ **Introduce new content progressively** (prerequisite-aware frontier)
- ✅ Track learner agency (audit trail)
- ✅ Balance strands under scarcity (re-normalization)
- ✅ Prevent plan drift (cached approvals)

## Next Steps

**Immediate**: Merge to `main` and tag release

**Post-merge nice-to-haves** (from ChatGPT's feedback):
- Migration runner (`state/migrate.py`) with version tracking
- Integration tests for preview→start→record flow
- Configurable skill mapping (YAML instead of hardcoded)
- Frontier explainability (why/why-not strings per node)
- Session analytics notebook (correlate preferences with outcomes)

## Files Changed

```
.github/workflows/ci.yml                    (new)
state/coach.py                               (modified)
state/session_planner.py                     (modified)
state/schema.sql                             (modified)
state/learner.yaml                           (modified)
state/migrations/003_skill_proficiency.sql   (new)
state/migrations/004_session_audit_trail.sql (new)
agents/bootstrap_items.py                    (modified)
LLanguageMe                                  (new)
scripts/viz_kg.py                            (new)
```

## Commit History

```
bfa89d1 feat: implement prerequisite-aware frontier filtering
9e3b7a5 style: apply ruff auto-fixes to coach.py and session_planner.py
1434598 feat: implement robustness improvements from ChatGPT review
e2517e3 docs: update session notes, status log, and CLAUDE.md
e7b476c feat: add skill-specific proficiency tracking with i-1 fluency filtering
c751e18 feat: add LLanguageMe launcher for session initialization
8cf5f66 feat: add weight normalization to adjust_focus()
7c72899 feat: add KG visualization tool
```

---

**Status**: ✅ Ready for PR to `main`
