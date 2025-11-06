# TODO: Spanish Learning Coach Development

*Last updated: 2025-11-06*
*Based on: SESSION_HANDOFF.md*

This document tracks planned improvements and features organized by priority. Items are drawn from the successful merge of prerequisite-aware curriculum features.

---

## 🚀 Immediate Priority (Validation)

These should be done first to validate the system works end-to-end:

### [ ] 1. Try a Real Learning Session
**Goal**: Validate end-to-end UX with yourself as learner

**Steps**:
```bash
./LLanguageMe          # Initialize session
# Follow instructions to start LLM session
# Try preview → start → practice → end flow
```

**What to check**:
- [ ] Frontier nodes appear in session plans
- [ ] Prerequisite chains unlock correctly
- [ ] CEFR filtering works as expected
- [ ] Strand balance converges to ~25% per strand
- [ ] Audit trail: `session_log` has JSON in `negotiated_weights` and `approved_plan`
- [ ] No errors or friction points

**Document findings** in SESSION_NOTES.md

---

## 🔧 Short-term Priority (Polish)

High ROI improvements from ChatGPT feedback. Tackle in order:

### [ ] 2. Migration Runner (`state/migrate.py`)
**Value**: Makes migrations one command instead of manual SQL
**Effort**: Low (1-2 hours)

**Features**:
- Auto-apply pending migrations in order
- Track schema version in database
- Create automatic backups before each migration
- Usage: `python state/migrate.py` applies all pending

**Files to create**:
- `state/migrate.py` - Main migration runner
- Update `state/schema.sql` to add `schema_version` table

---

### [ ] 3. Integration Tests for Session Flow
**Value**: Covers critical user journey
**Effort**: Medium (2-3 hours)

**Test coverage**:
- [ ] Test: `preview → adjust → start → record → end`
- [ ] Assert: audit fields round-trip correctly
- [ ] Assert: cached plan equals executed plan
- [ ] Assert: FSRS updates happen correctly
- [ ] Assert: mastery status transitions work

**Files to create**:
- `tests/test_session_integration.py`

---

### [ ] 4. Configurable Skill Mapping (YAML)
**Value**: Easy to adjust without code changes
**Effort**: Low-medium (2 hours)

**Implementation**:
- Move `infer_skill()` logic from `agents/bootstrap_items.py` to config
- Create `state/skill_mapping.yaml` with node type → skill rules
- Enables testing different mapping strategies
- Makes system more maintainable

**Files**:
- Create `state/skill_mapping.yaml`
- Update `agents/bootstrap_items.py` to read from YAML
- Add tests for different mappings

---

### [ ] 5. Frontier Explainability
**Value**: Helps debug selection and communicate with LLM
**Effort**: Medium (3 hours)

**Features**:
- Return "why included" / "why excluded" per node
- Example: `"excluded: missing prereq constr.es.present_indicative"`
- Add `explanation` field to frontier query results
- Helps learners understand why content is/isn't available

**Files to modify**:
- `state/session_planner.py`: Add explanation field to `get_frontier_nodes()`

---

## 📊 Medium-term Priority (Research)

Analytical and experimental work to validate design decisions:

### [ ] 6. Session Analytics
**Goal**: Validate learner agency hypothesis
**Effort**: Medium (4-5 hours)

**Analysis**:
- Notebook to analyze `negotiated_weights` correlation with quality/retention
- Track which preferences lead to better outcomes
- Guides future preference weight tuning
- Requires 20-30 real sessions of data

**Files to create**:
- `notebooks/session_analytics.ipynb`
- Queries on `session_log` + `exercise_log` + `review_history`

---

### [ ] 7. Convergence Testing
**Goal**: Validate progressive pressure algorithm
**Effort**: Medium (3-4 hours)

**Test approach**:
- Run 50 synthetic sessions with mock learner
- Assert strand balance converges to target (25% ± 5%)
- Track convergence rate and stability
- Identify edge cases where balance fails

**Files to create**:
- `tests/test_convergence.py`
- `scripts/run_synthetic_sessions.py`

---

### [ ] 8. Secure Level Promotion Analysis
**Goal**: Prevent oscillation between levels
**Effort**: Medium (3-4 hours)

**Improvements**:
- Track promotion frequency and accuracy
- Add confidence statistics (n items, recency)
- Consider time-based constraints (min 10 sessions at level)
- Alert if promotion/demotion cycles detected

**Files to modify**:
- `state/coach.py`: Add promotion metadata
- `state/learner.yaml`: Add promotion history

---

## 🎯 Future Work (Nice-to-Have)

Enhancements for later iterations:

### [ ] 9. MCP Server Integration for Frontier
**Current**: Frontier filtering is direct DB access
**Future**: Expose `kg.next()` via MCP for remote LLM access
**Blocker**: Works fine for local CLI orchestrator now

---

### [ ] 10. Fluency Speed Tracking
**Current**: FSRS + CEFR filtering provides good i-1 proxy
**Future**: Log latency/automaticity metrics for fluency exercises
**Value**: More precise fluency measurement

---

### [ ] 11. Multi-learner Support
**Current**: Assumes single learner in `state/learner.yaml`
**Future**: Support multiple learner profiles
**Use case**: Family/classroom usage

---

### [ ] 12. Guardrails for Starved Strands
**Issue**: If KG lacks content for a strand, it stays underrepresented
**Solution**: Suggest nodes to author when strand scarcity detected
**Output**: "Recommend adding 5 more meaning_input Topics to reach balance"

---

### [ ] 13. Console Script Entry Point
**Enhancement**: Install LLanguageMe as a console script
**Usage**: `pip install -e .` then just run `llanguageme`
**Requires**: Update `pyproject.toml` with console_scripts entry

---

### [ ] 14. IRT-based Skill Modeling
**Current**: FSRS + CEFR for fluency (simpler, ships immediately)
**Future**: IRT θ ability, b difficulty, P(success) ≥ 0.90
**Trigger**: Evidence shows CEFR filtering insufficient
**Decision documented**: SESSION_NOTES.md

---

## 📝 Documentation Todos

### [ ] 15. Update STATUS.md
Reflect successful merge of v0.3.0 features

### [ ] 16. Archive Handoff Docs
Move `SESSION_HANDOFF.md` and `HANDOFF_QUICK_REF.md` to `docs/handoffs/`

### [ ] 17. Create Contributing Guide
Add `CONTRIBUTING.md` with:
- Development workflow
- Testing requirements
- PR guidelines
- Code style conventions

---

## 🐛 Known Issues & Limitations

Track these for potential fixes:

### Current Limitations
1. **No MCP server integration** - Frontier filtering is direct DB access
   - Not blocking for local CLI orchestrator
   - Future: Remote LLM access

2. **Strand inference is hardcoded** - Logic in `infer_strand_from_node_type()`
   - Current: Covers all existing node types correctly
   - Future: Move to YAML config (see #4 above)

3. **No fluency speed tracking** - Doesn't log latency/automaticity metrics
   - Current: FSRS + CEFR filtering provides good i-1 proxy
   - Future: Add speed logging (see #10 above)

4. **No multi-learner support** - Assumes single learner
   - Current: Sufficient for personal exploration
   - Future: Support multiple profiles (see #11 above)

---

## 🎓 Research Questions

Open questions to explore with real usage data:

1. **Learner agency impact**: Do negotiated strand weights correlate with better retention?
2. **Promotion timing**: Is 80% mastery threshold optimal, or should it vary by skill?
3. **Preview cache TTL**: Is 5 minutes the right balance, or should it adapt to usage patterns?
4. **Frontier sorting**: Should nodes prioritize by dependency depth, CEFR level, or frequency?
5. **Strand convergence rate**: How many sessions until 25% balance is reached?

---

## ✅ Completed (Archive)

Move completed items here with completion date:

- [x] **Prerequisite-aware frontier filtering** (2025-11-06)
- [x] **Skill-specific proficiency tracking** (2025-11-06)
- [x] **i-1 fluency filtering** (2025-11-06)
- [x] **Session plan caching** (2025-11-06)
- [x] **Audit trail for learner agency** (2025-11-06)
- [x] **CI/CD pipeline** (2025-11-06)
- [x] **KG visualization tool** (2025-11-06)
- [x] **LLanguageMe launcher** (2025-11-06)

---

## 📅 Suggested Roadmap

**Week 1** (Validation):
1. Try real learning session
2. Migration runner
3. Integration tests

**Week 2** (Polish):
4. Configurable skill mapping
5. Frontier explainability
6. Update documentation

**Month 2** (Research):
7. Session analytics (requires data)
8. Convergence testing
9. Secure level promotion analysis

**Future** (As needed):
10-14. Nice-to-have enhancements based on usage feedback

---

## 📌 Quick Reference

**Priority levels**:
- 🚀 **Immediate**: Do first, validates system works
- 🔧 **Short-term**: High ROI polish items
- 📊 **Medium-term**: Research and analysis
- 🎯 **Future**: Nice-to-haves

**Estimated effort**:
- Low: 1-2 hours
- Medium: 3-5 hours
- High: 6+ hours

**To pick next task**:
1. Complete all Immediate items first
2. Pick Short-term items by ROI and dependencies
3. Medium-term items need real usage data
4. Future items are aspirational

---

*This TODO reflects the state after successful merge of prerequisite-aware curriculum features. Update regularly as items are completed or priorities shift.*
