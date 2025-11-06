-- SQLite Schema for Spaced Repetition System (SRS) with Four Strands Support
-- Based on Free Spaced Repetition Scheduler (FSRS) algorithm
-- Reference: https://github.com/open-spaced-repetition/fsrs4anki/wiki/The-Algorithm
-- Four Strands Reference: FOUR_STRANDS_REDESIGN.md

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Items table: tracks all learnable items (vocabulary, grammar, phrases, etc.)
CREATE TABLE IF NOT EXISTS items (
    item_id TEXT PRIMARY KEY,              -- Unique identifier for the item
    node_id TEXT NOT NULL,                 -- Reference to knowledge graph node
    type TEXT NOT NULL,                    -- Type: 'vocabulary', 'grammar', 'phrase', etc.
    last_review TIMESTAMP,                 -- Last time the item was reviewed (NULL if never reviewed)
    stability REAL DEFAULT 0.0,            -- FSRS stability parameter (in days)
    difficulty REAL DEFAULT 5.0,           -- FSRS difficulty parameter (0-10 scale)
    reps INTEGER DEFAULT 0,                -- Number of times reviewed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- When item was added to SRS

    -- Four Strands additions
    primary_strand TEXT,                   -- Primary strand: 'meaning_input', 'meaning_output', 'language_focused', 'fluency'
    mastery_status TEXT DEFAULT 'learning', -- Status: 'new', 'learning', 'mastered', 'fluency_ready'
    last_mastery_check TIMESTAMP,          -- Last time mastery status was evaluated

    FOREIGN KEY (node_id) REFERENCES knowledge_graph(node_id) ON DELETE CASCADE
);

-- Review history table: tracks all review attempts
CREATE TABLE IF NOT EXISTS review_history (
    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT NOT NULL,                 -- Item that was reviewed
    review_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    quality INTEGER NOT NULL,              -- Quality of recall (0-5 scale)
    stability_before REAL,                 -- Stability before this review
    stability_after REAL,                  -- Stability after this review
    difficulty_before REAL,                -- Difficulty before this review
    difficulty_after REAL,                 -- Difficulty after this review

    -- Four Strands additions
    strand TEXT,                           -- Strand context: 'meaning_input', 'meaning_output', 'language_focused', 'fluency'
    exercise_type TEXT,                    -- Type of exercise: 'controlled_drill', 'production', 'comprehension', 'speed_drill'

    FOREIGN KEY (item_id) REFERENCES items(item_id) ON DELETE CASCADE
);

-- Fluency metrics table: tracks speed and automaticity
CREATE TABLE IF NOT EXISTS fluency_metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT NOT NULL,
    session_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_seconds REAL NOT NULL,        -- How long the exercise took
    output_word_count INTEGER,             -- Number of words produced (if measurable)
    words_per_minute REAL,                 -- Calculated WPM
    pause_count INTEGER,                   -- Number of pauses (if measurable)
    hesitation_markers INTEGER,            -- Count of "um", "uh", etc. (if measurable)
    baseline_wpm REAL,                     -- Previous best WPM for comparison
    improvement_pct REAL,                  -- Percentage improvement from baseline
    smoothness TEXT,                       -- Self-assessment: 'automatic', 'some_pauses', 'struggled'
    improvement_feel TEXT,                 -- Self-assessment: 'easier', 'same', 'harder'
    notes TEXT,
    FOREIGN KEY (item_id) REFERENCES items(item_id) ON DELETE CASCADE
);

-- Meaning-input log table: tracks comprehension-focused practice
CREATE TABLE IF NOT EXISTS meaning_input_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id TEXT NOT NULL,                 -- Node practiced (may not have SRS item)
    item_id TEXT,                          -- Link to SRS item if applicable
    session_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    comprehension_quality INTEGER,         -- Quality rating (0-5 scale)
    understood_key_points BOOLEAN,         -- Did learner grasp key points?
    required_repetitions INTEGER,          -- How many repetitions needed
    task_type TEXT,                        -- 'comprehension', 'listening', 'reading'
    notes TEXT
);

-- Meaning-output log table: tracks communication-focused practice
CREATE TABLE IF NOT EXISTS meaning_output_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id TEXT NOT NULL,
    item_id TEXT,                          -- Link to SRS item if applicable
    session_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    communication_successful BOOLEAN,      -- Did learner convey their message?
    quality INTEGER,                       -- 0-5 scale
    errors_noted TEXT,                     -- JSON array of error types for tracking
    required_clarification BOOLEAN,        -- Did listener need clarification?
    task_type TEXT,                        -- 'conversation', 'role_play', 'presentation', etc.
    notes TEXT,
    FOREIGN KEY (item_id) REFERENCES items(item_id) ON DELETE SET NULL
);

-- Migration tracking table
CREATE TABLE IF NOT EXISTS schema_migrations (
    migration_id TEXT PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- Session log table: tracks complete session metadata
CREATE TABLE IF NOT EXISTS session_log (
    session_id TEXT PRIMARY KEY,
    learner_id TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    duration_target_min INTEGER,
    duration_actual_min REAL,
    exercises_planned INTEGER,
    exercises_completed INTEGER DEFAULT 0,
    strand_mi_pct REAL,                    -- Meaning-input percentage (0-100)
    strand_mo_pct REAL,                    -- Meaning-output percentage (0-100)
    strand_lf_pct REAL,                    -- Language-focused percentage (0-100)
    strand_fl_pct REAL,                    -- Fluency percentage (0-100)
    balance_status TEXT,                   -- 'balanced', 'slight_imbalance', 'severe_imbalance'
    quality_avg REAL,                      -- Average quality score across exercises
    mastery_changes INTEGER DEFAULT 0,     -- Number of items that changed mastery status
    notes TEXT
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Items table indexes
CREATE INDEX IF NOT EXISTS idx_items_node_id ON items(node_id);
CREATE INDEX IF NOT EXISTS idx_items_type ON items(type);
CREATE INDEX IF NOT EXISTS idx_items_last_review ON items(last_review);
CREATE INDEX IF NOT EXISTS idx_items_mastery_status ON items(mastery_status);
CREATE INDEX IF NOT EXISTS idx_items_strand ON items(primary_strand);

-- Review history indexes
CREATE INDEX IF NOT EXISTS idx_review_history_item_id ON review_history(item_id);
CREATE INDEX IF NOT EXISTS idx_review_history_time ON review_history(review_time);
CREATE INDEX IF NOT EXISTS idx_review_history_strand ON review_history(strand);

-- Fluency metrics indexes
CREATE INDEX IF NOT EXISTS idx_fluency_item_date ON fluency_metrics(item_id, session_date);
CREATE INDEX IF NOT EXISTS idx_fluency_date ON fluency_metrics(session_date);

-- Session log indexes
CREATE INDEX IF NOT EXISTS idx_session_log_learner ON session_log(learner_id);
CREATE INDEX IF NOT EXISTS idx_session_log_started ON session_log(started_at);

-- Meaning-input log indexes
CREATE INDEX IF NOT EXISTS idx_input_log_node ON meaning_input_log(node_id);
CREATE INDEX IF NOT EXISTS idx_input_log_item ON meaning_input_log(item_id);
CREATE INDEX IF NOT EXISTS idx_input_log_date ON meaning_input_log(session_date);

-- Meaning-output log indexes
CREATE INDEX IF NOT EXISTS idx_output_log_node ON meaning_output_log(node_id);
CREATE INDEX IF NOT EXISTS idx_output_log_date ON meaning_output_log(session_date);
CREATE INDEX IF NOT EXISTS idx_output_log_item ON meaning_output_log(item_id);

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View: Items due for review (original FSRS view)
CREATE VIEW IF NOT EXISTS due_items AS
SELECT
    i.item_id,
    i.node_id,
    i.type,
    i.last_review,
    i.stability,
    i.difficulty,
    i.reps,
    i.mastery_status,
    CASE
        WHEN i.last_review IS NULL THEN 1  -- New items are due
        ELSE julianday('now') - julianday(i.last_review) >= i.stability
    END AS is_due
FROM items i
WHERE is_due = 1
ORDER BY i.last_review ASC NULLS FIRST;

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
        120 as duration_seconds  -- Assume 2 min per comprehension exercise
    FROM meaning_input_log

    UNION ALL

    -- From meaning output
    SELECT
        session_date,
        'meaning_output' as strand,
        60 as duration_seconds  -- Assume 1 min per output exercise
    FROM meaning_output_log
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
