# Session Planner API

**Phase 2 Implementation**: Four Strands session planning with automatic strand balancing.

## Overview

The Session Planner creates balanced language learning sessions across Nation's Four Strands:

1. **Meaning-focused Input** (25%) - Comprehension activities (listening, reading)
2. **Meaning-focused Output** (25%) - Communication activities (speaking, writing)
3. **Language-focused Learning** (25%) - Explicit study (drills, grammar practice)
4. **Fluency Development** (25%) - Automaticity practice with mastered content

### Key Features

- **Progressive Pressure Algorithm**: Automatically rebalances strands when distribution deviates from target
- **Defeasible Recommendations**: Learner preferences can override system suggestions
- **Mastery Tracking**: Items progress from NEW → LEARNING → MASTERED → FLUENCY_READY
- **Flexible Criteria**: Mastery thresholds are configurable per learner

## Architecture

```
SessionPlanner
│
├── get_strand_balance()         # Analyze recent session distribution
├── calculate_strand_weights()   # Compute rebalancing pressure
├── plan_session()               # Generate complete session plan
│   ├── get_frontier_nodes()     # KG: nodes ready to learn
│   ├── get_due_items()          # SRS: items due for review
│   └── get_mastered_items()     # Items ready for fluency practice
│
└── Selection methods (per strand)
    ├── _select_meaning_input()
    ├── _select_meaning_output()
    ├── _select_language_focused()
    └── _select_fluency()
```

## Usage

### Basic Session Planning

```python
from pathlib import Path
from state.session_planner import SessionPlanner

# Initialize planner
planner = SessionPlanner(
    kg_db_path=Path("kg.sqlite"),
    mastery_db_path=Path("state/mastery.sqlite")
)

# Plan a 20-minute session
plan = planner.plan_session(
    learner_id="brett",
    duration_minutes=20
)

# Access plan details
print(f"Balance status: {plan.balance_status}")
print(f"Exercises: {len(plan.exercises)}")

for exercise in plan.exercises:
    print(f"  {exercise.strand}: {exercise.instructions}")
```

### Check Strand Balance

```python
# Get current strand distribution
balance = planner.get_strand_balance(
    learner_id="brett",
    last_n_sessions=10  # Analyze last 10 days
)

print(f"Meaning Input: {balance.meaning_input * 100:.1f}%")
print(f"Meaning Output: {balance.meaning_output * 100:.1f}%")
print(f"Language-focused: {balance.language_focused * 100:.1f}%")
print(f"Fluency: {balance.fluency * 100:.1f}%")
```

### Learner Preference Override

```python
# Learner wants more fluency practice
learner_pref = {
    'fluency': 2.0,           # High priority
    'meaning_output': 1.5,    # Medium-high
    'meaning_input': 1.0,     # Neutral
    'language_focused': 0.5   # Lower priority
}

plan = planner.plan_session(
    learner_id="brett",
    duration_minutes=20,
    learner_preference=learner_pref  # System gives 30% weight to this
)
```

### Update Mastery Status

```python
from state.session_planner import update_mastery_status

# Check if item has reached mastery
old_status, new_status = update_mastery_status(
    item_id="card.es.ser_vs_estar.001",
    db_path=Path("state/mastery.sqlite"),
    criteria={
        'stability_days': 21,   # 3 weeks retention
        'min_reps': 3,          # At least 3 successful reviews
        'avg_quality': 3.5      # Average quality >= 3.5/5
    }
)

if old_status != new_status:
    print(f"Item progressed: {old_status} → {new_status}")
```

### Custom Mastery Criteria

```python
# Initialize with custom thresholds
planner = SessionPlanner(
    kg_db_path=Path("kg.sqlite"),
    mastery_db_path=Path("state/mastery.sqlite"),
    mastery_criteria={
        'stability_days': 30,   # Stricter: 30 days instead of 21
        'min_reps': 5,          # More reviews required
        'avg_quality': 4.0      # Higher quality threshold
    }
)
```

## Data Structures

### StrandBalance

Tracks recent strand distribution:

```python
@dataclass
class StrandBalance:
    meaning_input: float      # Percentage (0.0-1.0)
    meaning_output: float
    language_focused: float
    fluency: float
    total_exercises: int
    total_seconds: float

    def get_percentage(self, strand: str) -> float
    def deviation_from_target(self, strand: str) -> float
```

### Exercise

Represents a single planned exercise:

```python
@dataclass
class Exercise:
    strand: str                      # Which strand this exercise addresses
    node_id: str                     # KG node ID
    item_id: Optional[str]           # SRS item ID (None for meaning-input)
    exercise_type: str               # 'comprehension', 'production', etc.
    duration_estimate_min: int       # Estimated minutes
    priority_score: float            # Selection priority
    instructions: str                # Human-readable prompt
    metadata: Dict                   # Additional context
```

### SessionPlan

Complete session with exercises:

```python
@dataclass
class SessionPlan:
    learner_id: str
    session_date: datetime
    duration_target_minutes: int
    exercises: List[Exercise]
    strand_balance: StrandBalance
    balance_status: str              # 'balanced', 'slight_imbalance', 'severe_imbalance'
    notes: str                       # Human-readable summary
```

## Progressive Pressure Algorithm

The planner uses **progressive pressure** to maintain strand balance without being rigid:

### Tolerance Zones

| Deviation from 25% | Weight Adjustment | Interpretation |
|-------------------|------------------|----------------|
| Within ±5% (20-30%) | 1.0 (neutral) | Acceptable balance |
| ±5-10% (15-20% or 30-35%) | 2x deviation | Gentle pressure |
| >10% (<15% or >35%) | 4x deviation | Strong pressure |

### Example

If a learner has practiced:
- Meaning Input: 10% (15% below target)
- Meaning Output: 30% (5% above target)
- Language-focused: 35% (10% above target)
- Fluency: 25% (on target)

The system calculates weights:
- Meaning Input: 1.0 + (0.15 × 4) = **1.60** (strong increase)
- Meaning Output: 1.0 + (-0.05 × 0) = **1.00** (within tolerance)
- Language-focused: 1.0 + (-0.10 × 2) = **0.80** (gentle decrease)
- Fluency: 1.0 + (0 × 0) = **1.00** (neutral)

The planner allocates more time to Meaning Input in the next session.

### Defeasibility

Learner preferences get **30% weight**, system gets **70%**:

```python
# System says: meaning_input weight = 1.60
# Learner says: meaning_input preference = 0.5

final_weight = (1.60 × 0.7) + (0.5 × 0.3)
             = 1.12 + 0.15
             = 1.27  # Compromises between system and learner
```

This ensures:
- System guidance is respected (rebalancing happens)
- Learner agency is preserved (they can influence priorities)

## Integration Points

### Knowledge Graph (KG Server)

**Required**: `get_frontier_nodes()` needs KG integration

The planner expects nodes with this structure:

```python
{
    "node_id": "vocab.es.hablar",
    "type": "Lexeme",
    "label": "hablar",
    "cefr_level": "A1",
    "primary_strand": "meaning_output",  # REQUIRED for strand filtering
    # ... other KG metadata
}
```

**Integration options:**

1. **MCP Server** (recommended): Call `kg.next(learner_id, k=20)` via MCP
2. **Direct database**: Query `kg.sqlite` for nodes where prerequisites are satisfied

See `session_planner.py:211` for integration notes.

### SRS Server

**Completed**: The SRS server now provides:

- `srs.due(learner_id, limit)` - Items due for review
- `srs.mastered(learner_id, limit)` - Items ready for fluency practice (NEW)

The `srs.mastered()` endpoint queries the `fluency_ready_items` view created by the Four Strands migration.

## Testing

Run the test suite:

```bash
python state/test_session_planner.py
```

This verifies:
- ✓ Strand balance calculation
- ✓ Progressive pressure algorithm
- ✓ Session planning
- ✓ Mastery status updates

Expected output (empty database):
- All functions work correctly
- No exercises selected (normal when database is empty)
- Balance shows 25% per strand (default when no history)

## Configuration

### Mastery Criteria

Default thresholds (Nation-informed):

```python
DEFAULT_MASTERY_CRITERIA = {
    'stability_days': 21,    # 3 weeks retention (Nation: "secure knowledge")
    'min_reps': 3,           # Multiple successful encounters
    'avg_quality': 3.5       # Consistently good recall (3.5/5 = 70%)
}
```

These can be overridden per learner or per session.

### Strand Balance

- **Target**: 25% per strand (Nation's recommendation)
- **Tolerance**: ±5% (20-30% acceptable)
- **Analysis window**: Last 10 sessions (configurable)

## Database Schema

The planner requires these tables/views from the Four Strands migration:

### Items Table Extensions

```sql
ALTER TABLE items ADD COLUMN primary_strand TEXT;
ALTER TABLE items ADD COLUMN mastery_status TEXT DEFAULT 'learning';
ALTER TABLE items ADD COLUMN last_mastery_check TIMESTAMP;
```

### Required Views

- `fluency_ready_items` - Mastered items (stability ≥21d, reps ≥3)
- `strand_balance_recent` - Recent strand distribution
- `strand_balance_summary` - Percentage summary

See `state/migrations/001_four_strands.sql` for full schema.

## Next Steps (Phase 3+)

1. **Phase 3: Assessment Logic**
   - Implement strand-specific assessment functions
   - Add quality scoring per exercise type
   - Log results to fluency_metrics, meaning_input_log, meaning_output_log

2. **Phase 4: Content Tagging**
   - Tag existing KG nodes with `primary_strand`
   - Classify exercises by strand appropriateness
   - Populate frequency/difficulty metadata

3. **Phase 5: Coaching Integration**
   - Rewrite SPANISH_COACH.md to use session planner
   - Update LLM orchestrator instructions
   - Test end-to-end lesson flow

4. **Phase 6: Measurement & Tuning**
   - Track actual vs. target strand balance
   - Calibrate pressure algorithm
   - Gather learner feedback on recommendations

## References

- **Design Document**: `FOUR_STRANDS_REDESIGN.md`
- **Migration**: `state/migrations/001_four_strands.sql`
- **Schema**: `state/schema.sql`
- **Paul Nation**: *The Four Strands* (Language Teaching Methodology)

## API Stability

This is **Phase 2 implementation**. API may change as we integrate with:
- KG server (frontier node structure)
- Coaching orchestrator (session flow)
- Assessment logic (exercise scoring)

Breaking changes will be documented in migration notes.
