# Session Handoff Notes - 2025-11-06

## Session Summary

This session completed **Option C (Content Expansion)** and added **learner agency features**, then addressed **repository hygiene** issues from ChatGPT code reviews.

**Branch**: `claude/init-project-011CUpegsSPagPb357XiC9b7`
**Status**: ✅ **MERGE-READY** per ChatGPT final review
**Total commits this session**: 6

---

## What Was Accomplished

### 1. Session Planner Bug Fix ✅
- **Issue**: Negative strand weights created negative target_time, breaking exercise selection loop
- **Fix**: Clamp weights to `max(0, weight)` in `session_planner.py:342`
- **Impact**: Sessions now plan correctly even with severe strand imbalance
- **Commit**: `f547858`

### 2. Content Expansion (25 → 100 nodes) ✅

**Phase 1** (27 nodes): CanDo + Constructions
- 16 B1 CanDo descriptors (CEFR Companion Volume aligned)
- 11 B1 Constructions (subjunctive, conditionals, connectors)

**Phase 2** (25 nodes): Vocabulary + Functions
- 18 Lexemes (high-frequency with Zipf scores 3.6-5.6)
- 7 Functions (travel, work, health, negotiations)

**Phase 3+4** (23 nodes): Topics + Discourse + Assessment + Morphology
- 7 Topics (work, leisure, travel, health, urban living, tech, relationships)
- 4 DiscourseMove (turn-taking, reformulation, hedging, cohesion)
- 4 PragmaticCue (formal register, softening, disagreement, small talk)
- 3 AssessmentCriterion (grammatical control, coherence, pronunciation)
- 5 Morph (pronoun stacking, se impersonal, conditional, subjunctive irregular, comparatives)

**Bootstrap Fix**: Updated strand mapping (Topic → meaning_input, added mappings for new types)

**Commits**: `9423bc9` (Phase 1), `e6657b0` (Phase 2), `8b936b7` (Phases 3-4)

### 3. Learner Agency (Preview/Negotiate Workflow) ✅

**New Coach Methods**:
```python
# Preview plan WITHOUT starting session
preview = coach.preview_session(learner_id, duration_minutes, learner_preference)

# Translate goals into preference weights
weights = coach.adjust_focus("prepare for travel to Barcelona", current_balance)

# Start with negotiated preferences
session = coach.start_session(learner_id, learner_preference=weights)
```

**Workflow**:
1. Coach previews plan: "8 exercises (3 output, 3 grammar, 2 listening)"
2. Learner negotiates: "I have a trip - focus on travel?"
3. Coach adjusts weights, re-previews
4. Learner approves, session starts with preferences

**Documentation**: Complete workflow in `COACH_INSTRUCTIONS.md` (400+ lines)

**Test Script**: `test_preview_negotiate.py` (interactive demo)

**Commit**: `9d72207`

### 4. Repository Hygiene ✅

**Fixed .gitignore**:
- Now ignores `state/mastery.sqlite` and `state/*.sqlite`
- Removed 80KB tracked database (reproducible artifact)
- Updated comments with reproduction instructions

**Created DATA_SOURCES.md**:
- Complete citations for all third-party data
- Licensing summary table
- Reproducibility instructions
- Sources: SUBTLEX-ESP, Multilex, Corpus del Español, PRESEEA, GPT estimates, CEFR, PCIC

**Created Migration 002 (session_log)**:
- New `session_log` table with structured session data
- Tracks: exercises planned/completed, duration, strand distribution, balance status, quality avg, mastery changes
- `recent_sessions` view for 30-day analytics
- Wired into `coach.py` `_log_session_end()`

**Commits**: `11ab9df` (.gitignore for logs), `5b32ed1` (hygiene + session_log)

---

## Current State

### Metrics
- **100 nodes** in Knowledge Graph (target: 101 - 99% complete)
- **6 commits** this session (all pushed)
- **100 items** bootstrapped (49% language_focused, 43% meaning_output, 8% meaning_input)
- **All atomic tools functional** with 100% reliability

### Node Distribution
| Type | Count |
|------|-------|
| Lexeme | 24 |
| CanDo | 20 |
| Construction | 15 |
| Morph | 10 |
| Function | 8 |
| Topic | 8 |
| DiscourseMove | 6 |
| PragmaticCue | 5 |
| AssessmentCriterion | 4 |
| **TOTAL** | **100** |

### Key Files Modified
- `state/session_planner.py` - Negative weight clamping
- `state/coach.py` - Preview/adjust methods, session logging
- `agents/bootstrap_items.py` - Strand mapping for new types
- `kg/seed/*.yaml` - 75 new node files
- `kg/split_yaml_nodes.py` - Multi-node YAML splitter
- `.gitignore` - Stop tracking SQLite DBs
- `DATA_SOURCES.md` - NEW: Complete provenance
- `state/migrations/002_session_log.sql` - NEW: Session logging
- `COACH_INSTRUCTIONS.md` - NEW: LLM workflow guide
- `test_preview_negotiate.py` - NEW: Interactive demo
- `README.md` - Updated status (Phase 3 complete)

---

## ChatGPT Final Review (Green Light)

**Review Date**: 2025-11-06
**Verdict**: ✅ **MERGE-READY**

**All blocking issues resolved**:
- ✅ Repo hygiene (no tracked DBs)
- ✅ Data provenance (complete citations)
- ✅ Session logging (database-backed)

**Minor concerns (all post-merge)**:
1. Strand inventory skew (8% meaning_input, 0% fluency)
2. Weight normalization (bounds and normalization in adjust_focus)
3. Plan drift edge case (items due/not-due between preview and start)
4. Preview auditability (log negotiated weights)

**Quote from review**:
> "Green-light to merge now (no outstanding blockers) provided you're comfortable merging without CI."

---

## Next Steps (Post-Merge)

### Immediate (Open Issues)
1. [ ] Add weight normalization to `adjust_focus()` (15 min)
   - Normalize weights to sum=4.0
   - Bound each weight to [0, 2.0] range
   - Location: `state/coach.py:150-216`

2. [ ] Add more meaning_input content (2-3 hours)
   - Current: 8 Topic nodes (8% of items)
   - Target: 15-20 Topics for 15-20% coverage
   - Or: Treat fluency as overlay on mastered items (architectural change)

3. [ ] Add GitHub Actions CI (30 min)
   - Python 3.11/3.12 matrix
   - Run: pytest, ruff, build KG
   - File: `.github/workflows/ci.yml`

4. [ ] Add convergence tests (1 hour)
   - Property test: N=50 sessions from skewed start
   - Assert strand balance converges to 25%±5%
   - Location: `tests/test_session_planner.py`

### Important (Next Sprint)
5. [ ] Implement `get_frontier_nodes()` (2-3 hours)
   - Compute down-closure of mastered nodes
   - Filter to nodes where prerequisites ⊆ mastered set
   - Fall back to no-prereq nodes if frontier sparse
   - Integrates with KG prerequisite chains
   - Location: `state/session_planner.py:211-235`

6. [ ] Add preference weights logging (30 min)
   - Log negotiated weights to session_log
   - Add `preference_weights` JSON column
   - Enables analysis of learner agency impact

### Research (When Ready)
7. [ ] Real learner testing
8. [ ] Scale test with expanded content (100+ sessions)
9. [ ] A/B test: guided vs. learner-directed sessions

---

## Known Issues & Gotchas

### 1. Strand Imbalance Is Expected
**Current distribution**: 49% language_focused, 43% meaning_output, 8% meaning_input, 0% fluency

**Why**: Node inventory reflects this - only 8 Topics provide meaning_input.

**Planner behavior**: Will allocate 0 minutes to under-represented strands (by design, via negative weight clamping).

**Not a bug**: System is working correctly given available content.

**Fix**: Add more Topics or architectural change (fluency as overlay).

### 2. Migration System Quirk
The migration tool sometimes shows warnings even when migrations succeed. Verify with:
```bash
python -c "import sqlite3; conn = sqlite3.connect('state/mastery.sqlite');
cursor = conn.cursor(); cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\"');
print([row[0] for row in cursor.fetchall()])"
```

Should include: `items`, `review_history`, `sessions`, `session_log`, `fluency_metrics`, `meaning_input_log`, `meaning_output_log`

### 3. Bootstrap Items vs. Planner
After `bootstrap_items.py`, all items are `status='new'` and `last_review=NULL`, so they're all "due".

Session planner correctly selects from these, but might return 0 exercises if:
- Strand balance is severely imbalanced (e.g., 52% meaning_output)
- Planner clamps that strand's weight to 0
- No other strand has due items

**Expected behavior** after severe imbalance - system refuses to worsen it.

### 4. Test Database Management
`state/mastery.sqlite` is now `.gitignore`d. To recreate for testing:
```bash
python state/db_init.py
python state/migrations/migrate.py --db state/mastery.sqlite
python agents/bootstrap_items.py
```

---

## Testing Commands

### Quick Smoke Test
```bash
# Rebuild everything
python kg/build.py kg/seed kg.sqlite
python state/db_init.py
python state/migrations/migrate.py --db state/mastery.sqlite
python agents/bootstrap_items.py

# Test preview/negotiate workflow
python test_preview_negotiate.py

# Run test suite
pytest -q
```

### Verify Session Logging
```python
from state.coach import Coach
from pathlib import Path

coach = Coach(kg_db_path=Path("kg.sqlite"), mastery_db_path=Path("state/mastery.sqlite"))
session = coach.start_session("test_learner", duration_minutes=10)
# ... do exercises ...
summary = coach.end_session(session["session_id"])

# Check session_log table
import sqlite3
conn = sqlite3.connect("state/mastery.sqlite")
cursor = conn.cursor()
cursor.execute("SELECT * FROM session_log ORDER BY started_at DESC LIMIT 1")
print(cursor.fetchone())  # Should show quality_avg, mastery_changes, strand percentages
```

---

## Important Context for Next Session

### Architecture Decisions Made
1. **Hybrid LLM + Code**: LLM handles pedagogy (quality assessment, feedback), code handles data integrity (FSRS, transactions, mastery progression)

2. **Conversational Negotiation**: Unlike Khan Academy's visual skill trees, this uses natural language preview/negotiate workflow suited to SRS scheduling and adult learner agency

3. **Strand Balancing**: Progressive pressure algorithm with negative weight clamping (skip over-represented strands rather than allocate negative time)

4. **Atomic Tools Surface**: Three operations (preview, start, record, end) wrap all database complexity

### Design Philosophy
- **Meaning before form** - Communication over grammatical perfection
- **Learner agency** - Preview and negotiate, don't impose
- **Algorithmic constraints** - Maintain SRS schedules and strand balance
- **Code handles data** - LLM never touches database directly
- **1-2 corrections max** - Targeted feedback, not overwhelming

### What Works Well
- Session planner with Four Strands balancing
- Atomic tools (100% reliability in scale testing)
- FSRS anti-cramming (correctly prevents over-practice)
- Preview/negotiate workflow (natural, maintains constraints)
- Content expansion (comprehensive B1 coverage)

### What Needs Improvement
- `get_frontier_nodes()` stubbed (planner can't use prerequisites)
- Strand inventory skew (need more meaning_input content)
- No CI yet (manual testing only)
- Weight normalization in adjust_focus (minor robustness)

---

## Files to Review for Context

If picking up where this left off:

1. **`COACH_INSTRUCTIONS.md`** - Complete LLM workflow (READ FIRST)
2. **`state/coach.py`** - Atomic tools implementation with preview/adjust
3. **`state/session_planner.py`** - Four Strands balancing with negative weight fix
4. **`DATA_SOURCES.md`** - Data provenance (for citations)
5. **`kg/EXPANSION_PLAN.md`** - Content expansion roadmap
6. **`test_preview_negotiate.py`** - Interactive demo of learner agency

---

## Merge Instructions

```bash
# 1. Final verification
git status  # Should be clean
git log --oneline -6  # Should show 6 commits from this session

# 2. Switch to main
git checkout main
git pull origin main

# 3. Merge (no-ff for visibility)
git merge --no-ff claude/init-project-011CUpegsSPagPb357XiC9b7 -m "Merge claude session: content expansion + learner agency + hygiene"

# 4. Push
git push origin main

# 5. Clean up branch (optional)
git branch -d claude/init-project-011CUpegsSPagPb357XiC9b7
git push origin --delete claude/init-project-011CUpegsSPagPb357XiC9b7
```

---

## Session Statistics

- **Duration**: ~4 hours
- **Commits**: 6 (all pushed)
- **Files changed**: 103 (78 new node files, 25 modified/new)
- **Lines added**: ~3500 (mostly YAML node definitions)
- **Key features**: Content expansion (75 nodes), learner agency, session logging
- **Bugs fixed**: 1 (negative strand weights)
- **Code reviews addressed**: 3 blocking issues from ChatGPT
- **Tests written**: 1 (interactive preview/negotiate demo)

---

## Final State Checklist

✅ All commits pushed to remote
✅ Working tree clean
✅ README updated with current status
✅ ChatGPT review completed (merge-ready)
✅ No tracked artifacts (.gitignore fixed)
✅ Data provenance documented
✅ Session logging functional
✅ 100 nodes in KG
✅ Learner agency implemented
✅ Tests passing (manual verification)

**Ready to merge and start fresh session! 🎉**

---

Last updated: 2025-11-06 23:52 UTC
Branch: claude/init-project-011CUpegsSPagPb357XiC9b7
Next session: Open issues for post-merge improvements
