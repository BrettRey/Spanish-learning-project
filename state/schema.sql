-- SQLite Schema for Spaced Repetition System (SRS)
-- Based on Free Spaced Repetition Scheduler (FSRS) algorithm
-- Reference: https://github.com/open-spaced-repetition/fsrs4anki/wiki/The-Algorithm

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
    FOREIGN KEY (item_id) REFERENCES items(item_id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_items_node_id ON items(node_id);
CREATE INDEX IF NOT EXISTS idx_items_type ON items(type);
CREATE INDEX IF NOT EXISTS idx_items_last_review ON items(last_review);
CREATE INDEX IF NOT EXISTS idx_review_history_item_id ON review_history(item_id);
CREATE INDEX IF NOT EXISTS idx_review_history_time ON review_history(review_time);

-- View for items due for review
CREATE VIEW IF NOT EXISTS due_items AS
SELECT
    i.item_id,
    i.node_id,
    i.type,
    i.last_review,
    i.stability,
    i.difficulty,
    i.reps,
    CASE
        WHEN i.last_review IS NULL THEN 1  -- New items are due
        ELSE julianday('now') - julianday(i.last_review) >= i.stability
    END AS is_due
FROM items i
WHERE is_due = 1
ORDER BY i.last_review ASC NULLS FIRST;
