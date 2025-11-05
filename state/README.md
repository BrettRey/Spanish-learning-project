# State Management for Spanish Learning System

This directory contains the state management components for the spaced repetition system (SRS), including learner profiles, mastery tracking, and the FSRS scheduling algorithm.

## Directory Structure

```
state/
├── README.md           # This file
├── schema.sql          # SQLite database schema
├── db_init.py          # Database initialization and utilities
├── fsrs.py            # FSRS algorithm implementation
├── learner.yaml       # Example learner profile
└── mastery.sqlite     # SQLite database (created at runtime)
```

## Database Schema

The system uses SQLite to track learner progress and schedule reviews efficiently.

### Tables

#### `items`
Tracks all learnable items in the SRS system.

- `item_id` (TEXT, PRIMARY KEY): Unique identifier for the item
- `node_id` (TEXT, NOT NULL): Reference to knowledge graph node
- `type` (TEXT, NOT NULL): Item type (vocabulary, grammar, phrase, etc.)
- `last_review` (TIMESTAMP): Last review time (NULL if never reviewed)
- `stability` (REAL): FSRS stability parameter in days (default: 0.0)
- `difficulty` (REAL): FSRS difficulty parameter, 0-10 scale (default: 5.0)
- `reps` (INTEGER): Number of times reviewed (default: 0)
- `created_at` (TIMESTAMP): When item was added to SRS

#### `review_history`
Complete audit trail of all review attempts.

- `review_id` (INTEGER, PRIMARY KEY): Auto-increment ID
- `item_id` (TEXT, NOT NULL): Item that was reviewed
- `review_time` (TIMESTAMP): When the review occurred
- `quality` (INTEGER, NOT NULL): Quality of recall (0-5 scale)
- `stability_before` (REAL): Stability before this review
- `stability_after` (REAL): Stability after this review
- `difficulty_before` (REAL): Difficulty before this review
- `difficulty_after` (REAL): Difficulty after this review

### Views

#### `due_items`
Automatically calculates which items are due for review based on:
- New items (never reviewed)
- Items where `elapsed_time >= stability`

## Learner Profile (learner.yaml)

The learner profile contains personalized settings and progress tracking:

### Core Information
- **learner_id**: Unique identifier
- **name**: Learner's display name
- **CEFR_goal**: Target proficiency level (A1-C2)
- **current_level**: Current proficiency level
- **L1**: Native language (for translation and error analysis)
- **correction_style**: Feedback preference (gentle, balanced, strict)

### Personalization
- **topics_of_interest**: List of topics for content personalization
- **learning_preferences**: Session length, daily goals, preferred times
- **error_patterns**: Common mistakes tracked by the system

### Progress Tracking
- **study_history**: Sessions, streaks, start date
- **vocabulary_stats**: Total words, active words, mastered words
- **grammar_stats**: Concepts learned and mastered

## FSRS Algorithm Implementation

The Free Spaced Repetition Scheduler (FSRS) is a modern, open-source algorithm for optimal review scheduling based on memory science.

### Core Concepts

1. **Stability (S)**: Time in days for retrievability to decay to 90%
   - Higher stability = longer intervals between reviews
   - Increases with successful reviews
   - Decreases with failed recalls

2. **Difficulty (D)**: Intrinsic difficulty of the item (0-10 scale)
   - Represents how hard an item is to remember
   - Adjusts based on review performance
   - Independent of current memory strength

3. **Retrievability (R)**: Probability of successful recall (0-1 scale)
   - Calculated based on elapsed time and stability
   - Decays exponentially over time
   - R = exp(ln(0.9) × elapsed_days / stability)

4. **Quality (Q)**: Self-rated recall quality (0-5 scale)
   - 0: Complete blackout (no memory)
   - 1: Incorrect, but answer seemed familiar
   - 2: Incorrect, but answer seemed easy to recall
   - 3: Correct, but required significant difficulty
   - 4: Correct, with some hesitation
   - 5: Perfect response, immediate recall

### Key Functions

#### `review_card(card, quality, review_time=None, w=DEFAULT_W)`
Main function that orchestrates the review process:
1. Calculates retrievability at review time
2. Updates stability based on quality and retrievability
3. Updates difficulty based on quality
4. Calculates next review date

**Example:**
```python
from datetime import datetime
from fsrs import ReviewCard, review_card

# Create a card with current state
card = ReviewCard(
    stability=5.0,
    difficulty=5.5,
    reps=3,
    last_review=datetime(2025, 11, 1)
)

# Process a review with quality 4 (correct with hesitation)
updated_card, result = review_card(card, quality=4)

print(f"New stability: {result.stability:.2f} days")
print(f"Next review: {result.next_review_date}")
print(f"Retrievability at review: {result.retrievability:.2%}")
```

#### `calculate_next_review_date(stability, current_time=None, request_retention=0.9)`
Calculates optimal next review date to maintain target retention (default 90%).

#### `initial_stability(quality, w=DEFAULT_W)`
Determines initial stability for new cards based on first review quality.

#### `initial_difficulty(quality, w=DEFAULT_W)`
Determines initial difficulty for new cards based on first review quality.

### Algorithm Advantages

1. **Evidence-based**: Based on extensive research data and memory science
2. **Adaptive**: Adjusts to individual item difficulty and learner performance
3. **Efficient**: Optimizes review timing to minimize study time while maximizing retention
4. **Transparent**: Open-source algorithm with clear mathematical formulas
5. **Predictive**: Tracks retrievability to predict memory strength

### Parameter Optimization

The `DEFAULT_W` parameters in `fsrs.py` are optimized from research data. These can be further tuned per learner using:
- Historical review data
- Gradient descent optimization
- Cross-validation to prevent overfitting

## Usage Examples

### Initialize Database

```python
from state.db_init import initialize_database

# Create the database with schema
initialize_database("state/mastery.sqlite")
```

### Add Items to SRS

```python
from state.db_init import add_item

# Add a vocabulary item
add_item(
    item_id="vocab_casa",
    node_id="es_noun_casa",
    item_type="vocabulary"
)
```

### Get Due Items

```python
from state.db_init import get_due_items

# Get all due items
due = get_due_items()

# Get 10 due vocabulary items
due_vocab = get_due_items(limit=10, item_type="vocabulary")
```

### Process a Review

```python
import sqlite3
from datetime import datetime
from state.fsrs import ReviewCard, review_card
from state.db_init import get_connection

# Get item from database
conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT * FROM items WHERE item_id = ?", ("vocab_casa",))
row = cursor.fetchone()

# Create card from database row
card = ReviewCard(
    stability=row["stability"],
    difficulty=row["difficulty"],
    reps=row["reps"],
    last_review=row["last_review"]
)

# Process review (user rated quality as 4)
updated_card, result = review_card(card, quality=4)

# Update database
cursor.execute("""
    UPDATE items
    SET stability = ?, difficulty = ?, reps = ?, last_review = ?
    WHERE item_id = ?
""", (
    updated_card.stability,
    updated_card.difficulty,
    updated_card.reps,
    updated_card.last_review,
    "vocab_casa"
))

# Record in review history
cursor.execute("""
    INSERT INTO review_history (
        item_id, review_time, quality,
        stability_before, stability_after,
        difficulty_before, difficulty_after
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
""", (
    "vocab_casa",
    result.next_review_date,
    4,
    card.stability,
    result.stability,
    card.difficulty,
    result.difficulty
))

conn.commit()
conn.close()
```

## Integration with Knowledge Graph

The SRS system integrates with the knowledge graph through the `node_id` foreign key:

- Each learnable item in the SRS references a node in the knowledge graph
- The knowledge graph provides semantic relationships and prerequisites
- The SRS tracks temporal learning progress for each node
- Combined, they enable intelligent content sequencing and personalization

## Performance Considerations

### Indexes
The schema includes indexes on:
- `node_id`: Fast lookup by knowledge graph node
- `type`: Fast filtering by item type
- `last_review`: Efficient due item calculations
- `review_time`: Quick access to review history

### Query Optimization
The `due_items` view pre-calculates due status using efficient SQLite date functions.

### Scalability
- SQLite handles thousands of items efficiently
- For 10,000+ items, consider adding composite indexes
- Review history can be archived periodically for long-term learners

## References

1. **FSRS Algorithm**: https://github.com/open-spaced-repetition/fsrs4anki/wiki/The-Algorithm
2. **Memory Research**: Piotr Wozniak's work on SuperMemo and spaced repetition
3. **FSRS Paper**: "A Stochastic Shortest Path Algorithm for Optimizing Spaced Repetition Scheduling"
4. **CEFR Framework**: https://www.coe.int/en/web/common-european-framework-reference-languages

## Future Enhancements

1. **Parameter Optimization**: Per-learner FSRS parameter tuning using historical data
2. **Adaptive Difficulty**: Automatic difficulty adjustment based on error patterns
3. **Load Balancing**: Distribute reviews evenly across days
4. **Forgetting Curves**: Visualize memory decay and learning progress
5. **Batch Operations**: Efficient bulk review processing
6. **Analytics Dashboard**: Detailed statistics and insights
