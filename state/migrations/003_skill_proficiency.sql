-- Migration 003: Skill-Specific Proficiency Tracking
-- Date: 2025-11-06
-- Description: Add skill column to items for skill-aware fluency filtering (i-1 principle)
-- Reference: Nation's Four Strands - fluency uses material below current proficiency

-- ============================================================================
-- PHASE 1: Add skill column to items table
-- ============================================================================

-- Track which skill(s) each item develops
-- This enables filtering fluency practice by secure_level per skill
-- following Nation's principle: fluency = automatic use of mastered content

ALTER TABLE items ADD COLUMN skill TEXT;
-- Values: 'reading', 'listening', 'speaking', 'writing'
-- NULL = not yet assigned (for backward compatibility)

-- ============================================================================
-- PHASE 2: Create index for skill-based queries
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_items_skill ON items(skill);

-- Combined index for fluency queries (skill + mastery + CEFR level via join)
CREATE INDEX IF NOT EXISTS idx_items_skill_mastery ON items(skill, mastery_status, stability);

-- ============================================================================
-- PHASE 3: Update fluency_ready_items view
-- ============================================================================

-- Drop old view
DROP VIEW IF EXISTS fluency_ready_items;

-- Recreate with skill awareness
-- Note: This view doesn't filter by CEFR yet (requires join with nodes table)
-- CEFR filtering happens in session_planner.py get_fluency_candidates()
CREATE VIEW IF NOT EXISTS fluency_ready_items AS
SELECT
    i.item_id,
    i.node_id,
    i.type,
    i.skill,
    i.stability,
    i.reps,
    i.difficulty,
    i.last_review,
    i.mastery_status
FROM items i
WHERE
    i.mastery_status IN ('mastered', 'fluency_ready')
    AND i.stability >= 21.0          -- At least 3 weeks retention
    AND i.reps >= 3                  -- Practiced multiple times
ORDER BY i.skill ASC, i.last_review ASC NULLS FIRST;

-- ============================================================================
-- PHASE 4: Migration notes
-- ============================================================================

-- This migration enables skill-specific proficiency tracking for i-1 filtering.
--
-- **Backward compatibility:**
-- - Existing items will have skill=NULL until re-bootstrapped or manually assigned
-- - Session planner will skip NULL skill items for fluency (safe default)
--
-- **Bootstrap strategy:**
-- - Update agents/bootstrap_items.py to infer skill from node type + strand
-- - Meaning-input → reading or listening (based on material type)
-- - Meaning-output → speaking or writing (based on exercise type)
-- - Language-focused → writing (form practice)
-- - Fluency → speaking (default)
--
-- **Fluency filtering algorithm (in session_planner.py):**
-- 1. Load secure_level for skill from learner.yaml (e.g., "A1")
-- 2. Query: items WHERE skill=? AND mastery='mastered' AND cefr_level <= secure_level
-- 3. This ensures fluency practice uses only i-1 or easier material
--
-- **Secure level promotion:**
-- - Every 10 sessions (or on-demand), check if 80% of next level is mastered
-- - If yes, promote secure_level (e.g., A1 → A2)
-- - Implemented in state/coach.py update_secure_levels()
