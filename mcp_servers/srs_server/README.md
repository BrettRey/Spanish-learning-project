# SRS MCP Server

A Model Context Protocol (MCP) server for managing spaced repetition learning using the FSRS (Free Spaced Repetition Scheduler) algorithm.

## Overview

This server provides three core tools for managing spaced repetition in language learning:

1. **srs.due** - Retrieve items due for review
2. **srs.update** - Update FSRS parameters after a review
3. **srs.stats** - Get comprehensive learner statistics

The server is designed to integrate with `../state/mastery.sqlite` but currently uses mock data for testing and development.

## Installation

No additional dependencies are required beyond Python 3.11+. The server uses only standard library modules.

```bash
# From project root
cd /Users/brettreynolds/Spanish-learning-project

# Activate virtual environment
source .venv/bin/activate

# Run the server
python -m mcp_servers.srs_server --help
```

## Usage

### Command Line Options

```bash
# Show help
python -m mcp_servers.srs_server --help

# Run test mode with sample queries
python -m mcp_servers.srs_server --test

# Run interactive demo
python -m mcp_servers.srs_server --demo

# Show available MCP tools
python -m mcp_servers.srs_server --show-tools

# Run with specific database (when available)
python -m mcp_servers.srs_server --db ../state/mastery.sqlite

# Show version
python -m mcp_servers.srs_server --version

# Set log level
python -m mcp_servers.srs_server --test --log-level DEBUG
```

### Quick Start

```bash
# 1. Test the server
python -m mcp_servers.srs_server --test

# 2. Try the interactive demo
python -m mcp_servers.srs_server --demo

# 3. View tool definitions
python -m mcp_servers.srs_server --show-tools
```

## MCP Tools

### 1. srs.due

Retrieve items due for review for a given learner.

**Parameters:**
- `learner_id` (string, required): Unique learner identifier
- `limit` (integer, optional): Maximum number of items to return (1-100, default: 10)

**Returns:** JSON string with list of due items

**Example Request:**
```python
from mcp_servers.srs_server import SRSServer

server = SRSServer()
result = server.get_due_items("brett", limit=5)
```

**Example Response:**
```json
{
  "items": [
    {
      "item_id": "card.es.ser_vs_estar.001",
      "node_id": "constr.es.copula_contrast",
      "type": "production",
      "last_review": "2025-11-01T10:00:00Z",
      "due_date": "2025-11-04T10:00:00Z",
      "fsrs_params": {
        "stability": 3.2,
        "difficulty": 5.1,
        "elapsed_days": 3,
        "scheduled_days": 3,
        "reps": 4,
        "lapses": 1,
        "state": 2
      }
    }
  ],
  "count": 1,
  "learner_id": "brett"
}
```

### 2. srs.update

Update FSRS parameters for an item after a review.

**Parameters:**
- `item_id` (string, required): Unique item identifier
- `quality` (integer, required): Review quality (0-5)
  - 0: Complete blackout (no recall)
  - 1: Incorrect response, but familiar
  - 2: Correct with serious difficulty
  - 3: Correct with some difficulty
  - 4: Correct with ease
  - 5: Perfect recall

**Returns:** JSON string with updated parameters and next review date

**Example Request:**
```python
result = server.update_item("card.es.ser_vs_estar.001", quality=4)
```

**Example Response:**
```json
{
  "success": true,
  "item_id": "card.es.ser_vs_estar.001",
  "quality": 4,
  "updated_params": {
    "stability": 8.0,
    "difficulty": 4.1,
    "elapsed_days": 0,
    "scheduled_days": 8,
    "reps": 5,
    "lapses": 1,
    "state": 2
  },
  "next_review_date": "2025-11-12T10:00:00Z",
  "days_until_next": 8
}
```

### 3. srs.stats

Get comprehensive learning statistics for a learner.

**Parameters:**
- `learner_id` (string, required): Unique learner identifier

**Returns:** JSON string with learner statistics

**Example Request:**
```python
result = server.get_stats("brett")
```

**Example Response:**
```json
{
  "learner_id": "brett",
  "total_items": 247,
  "due_count": 18,
  "new_count": 52,
  "learning_count": 31,
  "review_count": 164,
  "mastered_count": 89,
  "average_difficulty": 5.3,
  "reviews_today": 12,
  "streak_days": 7
}
```

## FSRS Algorithm Notes

### What is FSRS?

FSRS (Free Spaced Repetition Scheduler) is a modern spaced repetition algorithm that improves upon traditional SM-2. It uses a memory model based on three key concepts:

1. **Difficulty (D)**: How hard an item is for the learner (0-10)
2. **Stability (S)**: Current memory strength in days
3. **Retrievability (R)**: Probability of successful recall (calculated from S and elapsed time)

### Key Differences from SM-2

- **Dynamic difficulty adjustment**: Unlike SM-2's fixed easiness factor, FSRS adjusts difficulty based on actual performance
- **Power-law decay**: More realistic model of memory decay
- **Better handling of lapses**: Separate state tracking for relearning
- **Optimal scheduling**: Uses retrievability threshold to determine optimal review timing

### FSRS Parameters

Each item maintains the following parameters:

- **stability**: Memory strength (in days)
- **difficulty**: Item difficulty (0-10, higher = harder)
- **elapsed_days**: Days since last review
- **scheduled_days**: Days until next review
- **reps**: Total number of reviews
- **lapses**: Number of times forgotten
- **state**: Learning state
  - 0: New (never reviewed)
  - 1: Learning (first few reviews)
  - 2: Review (established memory)
  - 3: Relearning (after lapse)

### Algorithm Implementation

The current implementation uses a simplified FSRS model:

```python
# Stability adjustments based on quality
quality 0-1 (fail):  stability * 0.5, difficulty +2.0
quality 2 (hard):    stability * 1.2, difficulty +0.5
quality 3 (good):    stability * 1.5, difficulty unchanged
quality 4-5 (easy):  stability * 2.5, difficulty -1.0

# Next review interval = int(stability)
```

For production use, consider implementing the full FSRS algorithm with:
- Retrievability calculations
- Optimized stability increase formulas
- Per-learner parameter optimization

### References

- FSRS Paper: [https://github.com/open-spaced-repetition/fsrs4anki/wiki](https://github.com/open-spaced-repetition/fsrs4anki/wiki)
- Algorithm Details: [https://github.com/open-spaced-repetition/fsrs-rs](https://github.com/open-spaced-repetition/fsrs-rs)

## Integration Points

### Current State (Mock Data)

The server currently uses hard-coded mock data for testing. This allows:
- Development without database dependency
- Easy testing of tool interfaces
- Demonstration of expected behavior

### Future Integration with mastery.sqlite

To integrate with the real database:

1. **Database Schema**:
```sql
CREATE TABLE items (
    item_id TEXT PRIMARY KEY,
    learner_id TEXT NOT NULL,
    node_id TEXT NOT NULL,
    type TEXT NOT NULL,
    last_review TEXT,
    due_date TEXT,
    stability REAL,
    difficulty REAL,
    elapsed_days INTEGER,
    scheduled_days INTEGER,
    reps INTEGER,
    lapses INTEGER,
    state INTEGER
);

CREATE INDEX idx_learner_due ON items(learner_id, due_date);
CREATE INDEX idx_node ON items(node_id);
```

2. **Update `server.py`**:
   - Replace `_get_mock_items()` with SQLite queries
   - Add database connection pooling
   - Implement proper transaction handling
   - Add migration support

3. **Connection Management**:
```python
# In __init__
if self.db_path and Path(self.db_path).exists():
    self.conn = sqlite3.connect(self.db_path)
    self.conn.row_factory = sqlite3.Row
else:
    self.conn = None  # Use mock data
```

4. **Query Implementation**:
```python
def _get_due_items_from_db(self, learner_id: str, limit: int):
    cursor = self.conn.execute("""
        SELECT * FROM items
        WHERE learner_id = ?
        AND due_date <= datetime('now')
        ORDER BY due_date ASC
        LIMIT ?
    """, (learner_id, limit))
    return cursor.fetchall()
```

### Integration with Knowledge Graph

Items are linked to the knowledge graph via `node_id`:

```python
# Example: Get item context from KG
item = server.get_due_items("brett", limit=1)
node_id = item["items"][0]["node_id"]

# Query KG server for node details
kg_server.get_node(node_id)
# Returns: construction, prerequisites, prompts, etc.
```

### Integration with Curriculum Planner

The planner can use SRS data to inform curriculum decisions:

```python
# Get what's due
due_items = srs.due(learner_id="brett", limit=10)

# Get frontier from KG
frontier = kg.next(learner_id="brett", k=5)

# Interleave: 70% due items, 30% new frontier
lesson_plan = select_items(due_items, frontier, ratio=0.7)
```

### Integration with Coach/Assessor

After each interaction:

```python
# 1. Learner completes exercise
response = coach.run_exercise(item)

# 2. Assessor scores response
grade, rationale = assessor.score(response, rubric)

# 3. Update SRS parameters
quality = map_grade_to_quality(grade)  # Convert grade to 0-5
srs.update(item_id=item["item_id"], quality=quality)

# 4. Log evidence to KG
kg.add_evidence(node_id=item["node_id"], success=(quality >= 3))
```

## Error Handling

All tools return JSON responses with error information when issues occur:

```json
{
  "error": "Invalid learner_id",
  "message": "learner_id must be a non-empty string"
}
```

Common error scenarios:
- Invalid or missing parameters
- Database connection failures (future)
- Item not found (future)
- Concurrent update conflicts (future)

## Testing

### Run Built-in Tests

```bash
python -m mcp_servers.srs_server --test
```

This runs five test scenarios:
1. Get due items for a learner
2. Update item with good quality
3. Get learner statistics
4. Error handling: invalid learner_id
5. Error handling: invalid quality score

### Unit Tests (Future)

```bash
# When test suite is implemented
pytest mcp_servers/srs_server/tests/
```

### Integration Tests (Future)

Test with real database:

```bash
# Create test database
python scripts/init_test_db.py

# Run server with test DB
python -m mcp_servers.srs_server --db test_mastery.sqlite --test
```

## Logging

The server uses Python's standard logging module:

```bash
# Set log level
python -m mcp_servers.srs_server --test --log-level DEBUG

# Log output format
2025-11-04 10:00:00,000 - srs_server.server - INFO - Getting due items for learner_id=brett, limit=5
2025-11-04 10:00:00,001 - srs_server.server - INFO - Returning 3 due items
```

## Architecture

```
mcp_servers/srs_server/
├── __init__.py          # Package initialization, exports
├── __main__.py          # CLI entry point, argument parsing
├── server.py            # Core SRS logic, MCP tool implementations
└── README.md            # This file

Future additions:
├── db.py                # Database layer
├── fsrs.py              # Full FSRS algorithm implementation
├── tests/               # Unit and integration tests
│   ├── test_server.py
│   ├── test_fsrs.py
│   └── fixtures.py
└── migrations/          # Database schema migrations
    └── 001_initial.sql
```

## Performance Considerations

### Current (Mock Data)
- Response time: <1ms per request
- No persistence required
- Suitable for testing only

### Future (SQLite)
- Expected: <10ms per request with proper indexing
- Use connection pooling for concurrent requests
- Consider caching for frequently accessed learner stats
- Batch updates when possible

### Optimization Strategies

1. **Indexing**: Add indexes on `learner_id`, `due_date`, `node_id`
2. **Caching**: Cache learner stats with TTL
3. **Batch Operations**: Support bulk updates for multiple items
4. **Prepared Statements**: Reuse compiled queries
5. **Write-Ahead Logging**: Enable WAL mode for better concurrency

## Configuration (Future)

When database integration is complete, support configuration file:

```yaml
# srs_config.yaml
database:
  path: ../state/mastery.sqlite
  wal_mode: true
  cache_size: 2000

fsrs:
  initial_stability: 2.0
  initial_difficulty: 5.0
  retrievability_threshold: 0.9

scheduling:
  max_new_per_day: 20
  max_reviews_per_day: 100
  ease_bonus: 1.3
```

## Contributing

When extending this server:

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Include docstrings with examples
4. Update this README with new features
5. Add tests for new functionality

## License

Part of the Spanish Learning Project.

## Support

For issues or questions, see project documentation in the parent directory.
