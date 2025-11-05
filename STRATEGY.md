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
