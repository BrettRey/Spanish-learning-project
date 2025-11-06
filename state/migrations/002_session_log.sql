-- Migration 002: Session Logging
-- Date: 2025-11-05
-- Description: Add session_log table for tracking complete session data
-- Reference: ChatGPT code review - consolidate JSON logs into database

-- ============================================================================
-- PHASE 1: Create session_log table
-- ============================================================================

-- This table stores complete session metadata and results.
-- It complements the existing 'sessions' table (created in coach.py)
-- by adding structured storage for session summaries and metrics.

CREATE TABLE IF NOT EXISTS session_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL UNIQUE,
    learner_id TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    
    -- Session planning
    duration_target_min INTEGER NOT NULL,
    duration_actual_min REAL,
    exercises_planned INTEGER NOT NULL,
    exercises_completed INTEGER DEFAULT 0,
    
    -- Strand distribution (stored as percentages for quick queries)
    strand_mi_pct REAL,  -- meaning_input percentage
    strand_mo_pct REAL,  -- meaning_output percentage
    strand_lf_pct REAL,  -- language_focused percentage
    strand_fl_pct REAL,  -- fluency percentage
    
    -- Balance status
    balance_status TEXT,  -- 'balanced', 'slight_imbalance', 'severe_imbalance'
    
    -- Session summary
    quality_avg REAL,     -- Average quality across exercises
    mastery_changes INTEGER DEFAULT 0,  -- Number of items that changed mastery status
    
    -- Raw data (JSON for detailed analysis)
    exercises_json TEXT,  -- JSON array of exercise details
    summary_json TEXT,    -- JSON object with full session summary
    notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_session_log_learner ON session_log(learner_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_session_log_date ON session_log(started_at);
CREATE INDEX IF NOT EXISTS idx_session_log_balance ON session_log(balance_status, started_at);

-- ============================================================================
-- PHASE 2: Create view for recent session analytics
-- ============================================================================

-- View: Session statistics for the last 30 days
CREATE VIEW IF NOT EXISTS recent_sessions AS
SELECT 
    learner_id,
    COUNT(*) as session_count,
    SUM(exercises_completed) as total_exercises,
    AVG(duration_actual_min) as avg_duration_min,
    AVG(quality_avg) as avg_quality,
    AVG(strand_mi_pct) as avg_mi_pct,
    AVG(strand_mo_pct) as avg_mo_pct,
    AVG(strand_lf_pct) as avg_lf_pct,
    AVG(strand_fl_pct) as avg_fl_pct,
    SUM(CASE WHEN balance_status = 'balanced' THEN 1 ELSE 0 END) as balanced_sessions,
    SUM(CASE WHEN balance_status = 'severe_imbalance' THEN 1 ELSE 0 END) as imbalanced_sessions
FROM session_log
WHERE started_at >= DATE('now', '-30 days')
GROUP BY learner_id;

-- ============================================================================
-- PHASE 3: Migration notes
-- ============================================================================

-- This migration does NOT drop or modify the existing 'sessions' table
-- created dynamically in coach.py. The session_log table is additive.
--
-- Future work: Consider consolidating sessions + session_log into a single
-- table, but for now this provides backward compatibility.
--
-- To populate this table, update coach.py's end_session() method to insert
-- a row into session_log with the session summary data.
