-- Migration 004: Session Audit Trail
-- Date: 2025-11-06
-- Description: Add negotiated_weights and approved_plan to session_log for learner agency audit trail
-- Reference: ChatGPT review - track preview→start plan decisions

-- ============================================================================
-- PHASE 1: Add audit trail columns to session_log
-- ============================================================================

-- Track negotiated strand preference weights (from preview/adjust)
ALTER TABLE session_log ADD COLUMN negotiated_weights TEXT;
-- JSON format: {"meaning_input": 1.0, "meaning_output": 1.2, "language_focused": 0.8, "fluency": 1.0}

-- Track approved plan from preview (item IDs, strands, durations)
ALTER TABLE session_log ADD COLUMN approved_plan TEXT;
-- JSON format: [{"item_id": "...", "strand": "...", "duration_min": 2}, ...]

-- ============================================================================
-- PHASE 2: Migration notes
-- ============================================================================

-- These columns enable audit trail for learner agency:
-- 1. negotiated_weights: Documents how learner goals translated to strand emphasis
-- 2. approved_plan: Documents exact exercises approved in preview (before start)
--
-- **Use cases:**
-- - Analyze learner preferences over time
-- - Measure impact of learner agency on outcomes
-- - Debug plan drift issues (compare approved vs. actual)
-- - Research: correlation between goal negotiation and retention
--
-- **Populated by:**
-- - coach.start_session(): Logs negotiated weights and cached plan (if used)
-- - coach.end_session(): Already logs other session data
--
-- **Backward compatibility:**
-- - Existing session_log rows have NULL for these columns (acceptable)
-- - New sessions will populate both fields
