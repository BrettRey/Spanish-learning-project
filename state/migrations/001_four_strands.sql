-- Migration 001: Four Strands Redesign
-- Date: 2025-11-05
-- Description: Add strand tracking, fluency metrics, and mastery status
-- Reference: FOUR_STRANDS_REDESIGN.md

-- ============================================================================
-- PHASE 1: Extend items table
-- ============================================================================

-- Add strand metadata
ALTER TABLE items ADD COLUMN primary_strand TEXT;
-- Values: 'meaning_input', 'meaning_output', 'language_focused', 'fluency'

-- Add mastery status tracking
ALTER TABLE items ADD COLUMN mastery_status TEXT DEFAULT 'learning';
-- Values: 'new', 'learning', 'mastered', 'fluency_ready'

ALTER TABLE items ADD COLUMN last_mastery_check TIMESTAMP;

-- ============================================================================
-- PHASE 2: Create fluency_metrics table
-- ============================================================================

CREATE TABLE IF NOT EXISTS fluency_metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT NOT NULL,
    session_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_seconds REAL NOT NULL,
    output_word_count INTEGER,
    words_per_minute REAL,
    pause_count INTEGER,
    hesitation_markers INTEGER,
    baseline_wpm REAL,              -- Previous best for comparison
    improvement_pct REAL,            -- Percentage improvement from baseline
    smoothness TEXT,                 -- Self-assessment: 'automatic', 'some_pauses', 'struggled'
    improvement_feel TEXT,           -- Self-assessment: 'easier', 'same', 'harder'
    notes TEXT,
    FOREIGN KEY (item_id) REFERENCES items(item_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_fluency_item_date ON fluency_metrics(item_id, session_date);
CREATE INDEX IF NOT EXISTS idx_fluency_date ON fluency_metrics(session_date);

-- ============================================================================
-- PHASE 3: Create meaning_input_log table
-- ============================================================================

CREATE TABLE IF NOT EXISTS meaning_input_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id TEXT NOT NULL,
    session_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    understood BOOLEAN,              -- Did learner understand?
    comprehension_score REAL,        -- 0-3 scale: 0=didn't understand, 3=fully understood
    material_id TEXT,                -- e.g., 'podcast_travel_madrid_ep03'
    material_type TEXT,              -- 'audio', 'text', 'video'
    duration_minutes REAL,           -- How long was the material
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_input_log_node ON meaning_input_log(node_id);
CREATE INDEX IF NOT EXISTS idx_input_log_date ON meaning_input_log(session_date);

-- ============================================================================
-- PHASE 4: Create meaning_output_log table
-- ============================================================================

CREATE TABLE IF NOT EXISTS meaning_output_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id TEXT NOT NULL,
    item_id TEXT,                    -- Link to SRS item if applicable
    session_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    communication_successful BOOLEAN, -- Did learner convey their message?
    quality INTEGER,                 -- 0-5 scale
    errors_noted TEXT,               -- JSON array of error types for tracking
    required_clarification BOOLEAN,  -- Did listener need clarification?
    task_type TEXT,                  -- 'conversation', 'role_play', 'presentation', etc.
    notes TEXT,
    FOREIGN KEY (item_id) REFERENCES items(item_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_output_log_node ON meaning_output_log(node_id);
CREATE INDEX IF NOT EXISTS idx_output_log_date ON meaning_output_log(session_date);
CREATE INDEX IF NOT EXISTS idx_output_log_item ON meaning_output_log(item_id);

-- ============================================================================
-- PHASE 5: Extend review_history with strand context
-- ============================================================================

ALTER TABLE review_history ADD COLUMN strand TEXT;
-- Values: 'meaning_input', 'meaning_output', 'language_focused', 'fluency'

ALTER TABLE review_history ADD COLUMN exercise_type TEXT;
-- e.g., 'controlled_drill', 'production', 'comprehension', 'speed_drill'

-- ============================================================================
-- PHASE 6: Create views for session planning
-- ============================================================================

-- View: Mastered items ready for fluency practice
CREATE VIEW IF NOT EXISTS fluency_ready_items AS
SELECT
    i.item_id,
    i.node_id,
    i.type,
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
ORDER BY i.last_review ASC NULLS FIRST;

-- View: Items currently in learning phase
CREATE VIEW IF NOT EXISTS learning_items AS
SELECT
    i.item_id,
    i.node_id,
    i.type,
    i.stability,
    i.reps,
    i.difficulty,
    i.last_review,
    i.mastery_status
FROM items i
WHERE
    i.mastery_status IN ('new', 'learning')
    AND (i.reps < 3 OR i.stability < 21.0 OR i.stability IS NULL);

-- View: Recent strand balance (last 10 sessions)
CREATE VIEW IF NOT EXISTS strand_balance_recent AS
SELECT
    DATE(session_date) as session_day,
    strand,
    COUNT(*) as exercise_count,
    SUM(COALESCE(duration_seconds, 60)) as total_seconds
FROM (
    -- From review history (language-focused, meaning-output)
    SELECT
        review_time as session_date,
        strand,
        60 as duration_seconds  -- Assume 1 min per review
    FROM review_history
    WHERE strand IS NOT NULL

    UNION ALL

    -- From fluency metrics
    SELECT
        session_date,
        'fluency' as strand,
        duration_seconds
    FROM fluency_metrics

    UNION ALL

    -- From meaning input
    SELECT
        session_date,
        'meaning_input' as strand,
        COALESCE(duration_minutes * 60, 120) as duration_seconds  -- Default 2min
    FROM meaning_input_log

    UNION ALL

    -- From meaning output
    SELECT
        session_date,
        'meaning_output' as strand,
        60 as duration_seconds  -- Assume 1 min per output exercise
    FROM meaning_output_log
    WHERE strand IS NULL OR strand = 'meaning_output'
)
WHERE session_date >= datetime('now', '-10 days')
GROUP BY session_day, strand
ORDER BY session_day DESC, strand;

-- View: Strand balance summary (percentage distribution)
CREATE VIEW IF NOT EXISTS strand_balance_summary AS
SELECT
    strand,
    COUNT(*) as exercise_count,
    SUM(total_seconds) as total_seconds,
    ROUND(SUM(total_seconds) * 100.0 / (
        SELECT SUM(total_seconds)
        FROM strand_balance_recent
    ), 1) as percentage
FROM strand_balance_recent
GROUP BY strand;

-- View: Items needing mastery status update
CREATE VIEW IF NOT EXISTS items_needing_mastery_check AS
SELECT
    i.item_id,
    i.node_id,
    i.stability,
    i.reps,
    i.difficulty,
    i.mastery_status,
    i.last_review,
    i.last_mastery_check,
    AVG(rh.quality) as avg_quality
FROM items i
LEFT JOIN review_history rh ON i.item_id = rh.item_id
WHERE
    i.mastery_status != 'mastered'
    AND (
        i.last_mastery_check IS NULL
        OR julianday('now') - julianday(i.last_mastery_check) >= 1  -- Check daily
    )
GROUP BY i.item_id
HAVING
    i.reps >= 3
    AND i.stability >= 21.0
    AND avg_quality >= 3.5;

-- ============================================================================
-- MIGRATION METADATA
-- ============================================================================

CREATE TABLE IF NOT EXISTS schema_migrations (
    migration_id TEXT PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT INTO schema_migrations (migration_id, description)
VALUES ('001_four_strands', 'Add Four Strands support: strand tracking, fluency metrics, mastery status');
