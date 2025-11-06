# Strategic Direction & Exploration

This document captures strategic thinking, constraints, and experimental directions for the Spanish learning project.

**Last Updated**: 2025-11-05

---

## Project Context

### Purpose
- **Primary**: Personal exploration and learning project for understanding AI tooling capabilities
- **Secondary**: Test bed for ideas that might inform future work (e.g., Humber EAP program)
- **Nature**: Hobby/research project with no hard deadlines

### User
- Currently: Brett (solo user, self-directed learning)
- Future: Potentially Humber College EAP students (English, not Spanish)

### Key Constraints for Future Humber Deployment
- **Must use**: Microsoft Copilot (students have MS accounts)
- **Cannot use**: Claude API or other services requiring account creation
- **Cost**: Leverage existing MS licenses, avoid marginal costs
- **Goal**: Replace expensive Rosetta Stone with MS-based solution
- **Note**: These constraints apply to future Humber work, NOT current Spanish POC

---

## Current State Assessment (2025-11-05)

### What Exists (12,900+ lines, solid infrastructure)
- ✅ Knowledge graph build system (YAML → SQLite)
- ✅ Full FSRS algorithm implementation
- ✅ Three MCP servers (KG, SRS, Speech) with working APIs
- ✅ 65 tests with fixtures and good coverage
- ✅ Frequency database (4 sources: SUBTLEX, Multilex, GPT, Corpus del Español)
- ✅ PRESEEA corpus with speaker metadata and sampling tools
- ✅ 25 Spanish KG nodes (A1-B1 level, ~665 lines YAML)
- ✅ 6 lesson templates, 3 evaluation rubrics

### What's Missing
- ❌ **No orchestrator** to tie components together
- ❌ No way for a learner to actually use the system end-to-end
- ❌ No lesson session loop implemented
- ❌ MCP servers tested standalone but never used in integrated flow

### Observation
**Excellent plumbing, minimal curriculum, no conductor.**

---

## Strategic Insight: LLM as Orchestrator (2025-11-05)

### The Question
> "Could an LLM (CLI) be the missing conductor? Like instead of trying to code everything, could you just spin up an agent in this repo and say 'you're the teacher, here's your curriculum, I'm your student. go.'?"

### The Answer
**YES**, and this aligns with the original vision from `idea.md`:

Original vision:
- "Codex CLI for the live lesson/conversation (terminal or IDE), guided by an `AGENTS.md` in your repo"
- "Codex keeps state across turns and can run local commands/tests"
- MCP servers expose KG queries, SRS scheduling, speech processing

Modern equivalent:
- **Claude Code (or similar LLM CLI) = the orchestrator**
- MCP servers remain as tools for curriculum/scheduling/speech
- No need to code complex orchestration logic
- AI conducts lessons conversationally, following pedagogical rules from instructions

### Architecture Pattern

```
User: "Start a Spanish lesson"
  ↓
LLM CLI (Claude Code):
  1. Calls kg.next(learner_id, k=3) → gets learnable nodes
  2. Calls kg.prompt(node_id) → gets exercise scaffold
  3. Presents exercise conversationally
  4. Receives user response in Spanish
  5. Assesses quality (0-5) following SLA principles
  6. Calls srs.update(item_id, quality)
  7. Calls kg.add_evidence(node_id, success)
  8. Repeat for 20-minute session
```

### What This Tests
- Can AI follow complex pedagogical rules consistently?
- Does MCP architecture work for stateful, multi-turn tutoring?
- What's the UX of AI-as-teacher vs. coded rule engines?
- Where does AI shine vs. where you need deterministic code?
- How to write effective "AI agent instructions"?

### Implementation Approach
1. Create `SPANISH_COACH.md` with agent instructions (pedagogical rules, tool usage, session flow)
2. Fix bug in MCP server CLI (see Bugs section below)
3. Test with existing 25 nodes
4. Iterate based on what works/breaks

### Implications for Humber
- If "LLM as orchestrator" works, same pattern applies with MS Copilot
- Tests whether AI can handle nuanced pedagogical decisions
- Validates whether KG + SRS + LLM architecture is viable
- Informs what needs to be English-specific vs. language-agnostic

---

## Hybrid Architecture: LLM + Atomic Tools (2025-11-05)

### The Reliability Problem

**Question**: How faithfully will an LLM CLI maintain database hygiene?

**Honest Assessment**: LLMs will be ~85-90% faithful at calling tools, but ~60-70% at complex multi-step protocols like "update FSRS parameters AND mastery status AND log to strand table AND check for promotion to fluency queue."

### Where LLMs Will Struggle

**Database Hygiene Discipline:**
- Forgetting to update `last_mastery_check` timestamp
- Inconsistently logging to all three strand tables
- Skipping metadata recording when conversation diverges
- Remembering to call `srs.update()` after every single review

**Calculation Consistency:**
- Scoring quality (0-5) differently based on mood/phrasing
- Sometimes calling `session_planner.plan_session()`, sometimes improvising
- Complex conditional logic ("if mastered AND fluency-ready AND not recently practiced...")

**Pattern**: Works *most* of the time, but occasional lapses when:
- Conversation gets sidetracked mid-exercise
- Learner asks meta-questions
- Session ends abruptly

### Where LLMs Will Excel

**Adaptive Intelligence:**
- Natural error recovery from edge cases
- Graceful handling of missing data
- Asking clarifying questions when uncertain
- Adapting difficulty to learner level on the fly

**Conversational Teaching:**
- Natural pacing and motivation
- Implicit recasts and corrections
- Building on previous exercises
- Maintaining session continuity

**Structured Output:**
- Following templates reliably when prompted
- Calling tools with correct parameters
- Adhering to quality scales (0-5) when reminded

### The "What Would Nation Do?" Lens

Paul Nation's research suggests:

**Large quantities >> Precision:**
- 1000 exercises logged with 90% accuracy beats 100 exercises logged perfectly
- The goal is cumulative exposure, not perfect tracking
- Strand balance within ±10% is fine (our ±5% tolerance may be overkill)

**Learner perception is valid data:**
- Self-reporting "this felt faster" is meaningful signal
- Nation used stopwatches and surveys, not sophisticated instrumentation
- Subjective improvement assessments are research-grade

**Good enough to be useful:**
- FSRS works even with occasional missing data
- Strand balance self-corrects over time (progressive pressure)
- A few forgotten `srs.update()` calls won't break the system

### Solution: Atomic Tool Wrapper

**Don't ask LLM to:**
- Manually construct SQL
- Remember to update 4 related tables
- Implement complex conditional logic
- Track multi-step state machines

**Instead, provide atomic operations:**

```python
# ❌ BAD: LLM has to remember 4 separate calls
llm_calls_srs_update(item_id, quality)
llm_calls_log_fluency(item_id, duration, wpm)
llm_calls_check_mastery(item_id)
llm_calls_update_strand_balance(strand, duration)

# ✅ GOOD: One atomic operation, code handles everything
result = coach.record_exercise(
    item_id="card.es.ser_vs_estar.001",
    learner_response="Era un día soleado",
    quality=4,  # LLM's pedagogical judgment
    duration_seconds=45,
    strand="meaning_output"
)

# Returns everything LLM needs to know:
{
    "next_review": "2025-11-08T10:00Z",
    "new_stability": 2.8,
    "mastery_status": "learning",
    "strand_balance": {
        "meaning_output": 0.28  # Gentle reminder if imbalanced
    },
    "feedback": "Good progress! This item is becoming more stable."
}
```

### Division of Labor

**LLM Responsibilities (Pedagogical):**
1. Conduct conversational lessons
2. Generate contextual exercises
3. Assess quality (0-5 scale)
4. Provide feedback and corrections
5. Adapt pacing to learner needs
6. Maintain motivation and engagement

**Code Responsibilities (Data Integrity):**
1. All database writes
2. FSRS calculations and scheduling
3. Mastery status progression
4. Strand balance tracking
5. Session statistics and logging
6. Data validation and consistency

**Tools Bridge the Gap:**
- Simple, atomic operations
- LLM calls tools with minimal parameters (quality score, learner response)
- Code handles all the bookkeeping
- Return values give LLM context for next move

### Atomic Tool Design Principles

**1. Single Responsibility**
Each tool does ONE complete thing:
- `coach.record_exercise()` - Complete exercise lifecycle
- `coach.start_session()` - Initialize session, return plan
- `coach.end_session()` - Finalize stats, save logs

**2. Minimal LLM Input**
LLM only provides what only LLM can judge:
- Quality assessment (pedagogical judgment)
- Learner response text (for logging)
- Exercise context (which prompt was used)

**3. Comprehensive Output**
Return everything LLM needs for next decision:
- Next review scheduling
- Strand balance status
- Session progress
- Suggested next exercise

**4. Transactional**
Each tool call is atomic:
- All related tables updated together
- Rollback on error
- No partial states

### Implementation Strategy

**Phase 2.5: Atomic Coaching Tools** (new intermediate phase)
- Create `state/coach.py` wrapper module
- Implement atomic operations:
  - `start_session(learner_id, duration_minutes)`
  - `record_exercise(item_id, quality, response, duration, strand)`
  - `end_session(session_id)`
- Wrap session_planner, FSRS, and logging in single calls
- Test with sample data

**Then Phase 3: LLM Integration**
- Update `SPANISH_COACH.md` to use atomic tools
- Test LLM reliability with new interface
- Measure: How often does LLM correctly call tools vs. improvise?

### Expected Outcomes

**Reliability:**
- Database consistency: 95%+ (code-enforced)
- Tool usage: 85-90% (LLM remembers to call tools)
- Quality scoring: 70-80% consistency (LLM judgment varies)

**Benefits:**
- Nation-grade tracking (good enough for research)
- LLM-grade pedagogy (adaptive, conversational, engaging)
- Clean separation of concerns
- Easy to debug (deterministic data layer)

**Trade-offs:**
- Less flexible than pure LLM improvisation
- Need to design tool API carefully
- Tools become system's constraint boundary

### Why This Works

**Plays to strengths:**
- LLM does what LLM does best (conversation, adaptation)
- Code does what code does best (consistency, calculation)

**Nation-compatible:**
- Simple, practical measurement
- Large quantities with good-enough accuracy
- Learner perception valued

**Debuggable:**
- Database stays consistent (code writes it)
- Logs show exactly what LLM called
- Can track LLM reliability over time

**Scalable:**
- Add new exercises without changing tools
- Refine tool implementation without changing LLM instructions
- Same pattern works for MS Copilot (Humber future)

---

## Strategic Questions to Explore

### 1. Content vs. Code
- **Current**: 25 nodes manually authored (~665 lines YAML)
- **Target**: `phase_I_landscape.md` envisions ~100+ for B1 coverage
- **Infrastructure exists**: `kg/descriptors/` for automated generation (not implemented)
- **Question**: Is the interesting problem "authoring curriculum at scale" or "orchestration patterns"?

### 2. Corpus/Frequency Tooling ROI
- **Invested in**: PRESEEA corpus, frequency databases from 4 sources, demographic sampling
- **Question**: Does this actually improve learning outcomes or is it premature optimization?
- **Experiment**: Compare lessons with/without corpus examples

### 3. MCP as Integration Pattern
- **Built**: MCP servers with clean APIs
- **Not tested**: How well does MCP work for stateful, multi-turn interactions?
- **Question**: What breaks? What's elegant vs. clunky in practice?

### 4. Transferability to English EAP
- Spanish: Morphology-heavy (verb conjugations, gender agreement)
- English EAP: Different structure (articles, prepositions, academic register)
- **Question**: How much of KG architecture transfers vs. is Spanish-specific?
- **Dependencies**: Likely need different node types, edge semantics

---

## Alternative Paths Considered (2025-11-05)

### Option A: Code the Orchestrator
Build Python script that calls MCP tools sequentially.
- **Pros**: Full control, deterministic
- **Cons**: Need to handle all edge cases, conversation flow, adaptation
- **Timeline**: 1-2 weeks for basic CLI

### Option B: LLM as Conductor (Selected for Exploration)
Use Claude Code (or similar) as conversational coach with MCP tools.
- **Pros**: Natural conversation, adaptive, tests AI pedagogy
- **Cons**: Less deterministic, depends on AI capabilities
- **Timeline**: Days to test initial concept
- **Status**: Chosen for next exploration

### Option C: Radical Simplification
Pick ONE skill, 10 nodes, simplest possible manual testing.
- **Pros**: Fastest user feedback
- **Cons**: Doesn't test infrastructure integration

### Option D: Content-First
Plan all B1 curriculum in CSV/Excel, test manually before automating.
- **Pros**: Validates pedagogy before engineering
- **Cons**: Delays learning about orchestration challenges

### Option E: Research Platform
Pivot to visualization/authoring tool for SLA researchers.
- **Pros**: Different market, clearer scope
- **Cons**: Not the original vision

---

## Bugs Found

### MCP Server CLI Bug (2025-11-05)
**File**: `mcp_servers/kg_server/__main__.py` line 314
**Issue**: Passes `use_mock_data` parameter to `KGServer.__init__()` but constructor doesn't accept it
**Impact**: `--test` and `--no-mock` flags don't work
**Cause**: Server was updated to use real databases, but CLI wasn't updated
**Status**: Needs fix

Similar issue likely exists in other server CLIs.

---

## Next Experiments

### Immediate (This Week)
1. Fix MCP server CLI bugs
2. Create `SPANISH_COACH.md` with agent instructions for conducting lessons
3. Test "LLM as conductor" pattern with existing 25 nodes
4. Document what works/breaks in actual lesson sessions

### Near-Term (If LLM Orchestration Works)
1. Identify which nodes are actually useful vs. theoretical
2. Add 10-15 nodes for one focused skill area (e.g., past-tense narration)
3. Refine agent instructions based on lessons learned
4. Document validated lesson flow patterns

### Open Questions
- How much determinism do we need vs. AI flexibility?
- Can AI maintain consistent quality assessments (0-5 scale)?
- Does FSRS actually work when AI controls the scheduling?
- What pedagogical rules can AI follow vs. what needs to be hardcoded?

---

## Learning Timeline Observation

From project owner:
> "My experience with LLM timeline estimates is that they're hilariously wrong, extrapolating from the pre-LLM era, and not taking into account the massive LLM-driven speed up. Like the repo you see was no more than three hours of my time."

**Implication**: Traditional software estimation (weeks for orchestrator) may be obsolete. LLM-assisted development enables much faster iteration. Stay experimental and keep cycles tight.

---

## References

- `idea.md`: Original vision (Codex + Agents SDK + MCP)
- `STATUS.md`: Implementation timeline and completed work
- `kg/phase_I_landscape.md`: B1 curriculum expansion roadmap
- `IMPLEMENTATION_SUMMARY.md`: Detailed build summary from initial implementation
