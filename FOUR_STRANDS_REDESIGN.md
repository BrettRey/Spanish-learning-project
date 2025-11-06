# Four Strands Redesign

**Date**: 2025-11-05
**Status**: Design Phase
**Goal**: Redesign Spanish learning system around Nation's Four Strands with proper mastery tracking

**Guiding Principle**: What Would Nation Do? (WWND)

---

## Design Philosophy: What Would Nation Do?

When facing design decisions, we apply Nation's research-based principles:

1. **Balance over perfection**: ~25% per strand matters more than exact precision
2. **Learner autonomy**: System suggests, learner decides (defeasible recommendations)
3. **Practical simplicity**: Stopwatch beats complex measurement systems
4. **Large quantities**: Amount of practice >> precision of assessment
5. **Learner perception is valid**: Subjective "getting faster" is meaningful data
6. **Sufficient practice, not perfect mastery**: If you can use it communicatively, it's mastered enough
7. **Natural recycling**: Strands recycle content organically (don't force rigid sequencing)
8. **Measurement serves learning**: Track what helps learners, not what's easiest to measure

**Applied to our design**:
- Strand balance: Flexible ±5% with self-correcting pressure (not rigid 25.0%)
- Mastery thresholds: Research-informed defaults, learner-adjustable (not one-size-fits-all)
- Fluency measurement: Self-timing + subjective feel (not waiting for speech recognition)
- Content curation: Start practical (links), evolve toward generation (not perfect library first)

---

## Executive Summary

Current system conflates all language learning into one undifferentiated "practice" category. This redesign restructures the entire system around **Nation's Four Strands** framework:

1. **Meaning-focused Input** (comprehension)
2. **Meaning-focused Output** (communication)
3. **Language-focused Learning** (explicit study)
4. **Fluency Development** (automaticity)

**Key Changes:**
- Every KG node tagged with strand(s)
- Session planning balances strands (≈25% each)
- Different assessment criteria per strand
- FSRS integration for all strands
- Fluency tracking with self-assessment + timing
- Mastery thresholds determine progression paths

---

## Nation's Four Strands Framework

### Theoretical Foundation

From Paul Nation's extensive SLA research, effective language learning requires **balanced practice** across four complementary strands. Each strand serves a distinct purpose and requires different pedagogical approaches.

### The Four Strands

#### 1. Meaning-focused Input (25% of class time)
**Purpose**: Comprehension, vocabulary acquisition through context

**Characteristics:**
- Focus on understanding messages, not form
- 98%+ known vocabulary (i+1 level)
- Minimal interruption for instruction
- Large quantities of input
- Interesting, engaging content

**Activities:**
- Extensive listening
- Graded reading
- Watching videos with comprehension checks
- Story listening

**Assessment focus:**
- Did you understand the main ideas?
- Can you answer comprehension questions?
- Form/accuracy NOT assessed

**Example exercises:**
- Listen to podcast about Spanish cuisine, answer questions
- Read short story at your level, summarize
- Watch telenovela clip, discuss what happened

#### 2. Meaning-focused Output (25% of class time)
**Purpose**: Communication practice, pushing production, negotiation of meaning

**Characteristics:**
- Focus on conveying messages successfully
- Communicative pressure to be understood
- Stretching beyond current competence
- Real or simulated authentic tasks
- Listener/reader response is key

**Activities:**
- Conversations
- Role-plays
- Presentations
- Writing emails/messages
- Information gap tasks

**Assessment focus:**
- Did you communicate your message successfully?
- Did you adapt when misunderstood?
- Form matters only if it impedes communication

**Example exercises:**
- Role-play: resolve a hotel booking issue
- Describe your weekend plans to a partner
- Write recommendation for a restaurant

#### 3. Language-focused Learning (25% of class time)
**Purpose**: Explicit attention to linguistic features (form, meaning, use)

**Characteristics:**
- Direct focus on language forms
- Deliberate study
- Metalinguistic awareness
- Grammar explanations
- Vocabulary memorization
- Error correction matters

**Activities:**
- Grammar explanations and drills
- Vocabulary study with flashcards
- Error correction exercises
- Form-focused tasks (fill-in-blank, transformations)
- Pronunciation practice

**Assessment focus:**
- Accuracy of form
- Correct application of rules
- Precise vocabulary use
- Quality rating (0-5) with detailed feedback

**Example exercises:**
- Practice preterite vs. imperfect distinction
- Memorize subjunctive triggers
- Drilling verb conjugations

#### 4. Fluency Development (25% of class time)
**Purpose**: Automaticity, speed, confidence with **known** language

**Characteristics:**
- Use language you ALREADY KNOW
- Time pressure / speed focus
- Large quantities of easy practice
- Minimal hesitation / planning
- Errors are tolerated (speed over accuracy)
- Measurable improvement in rate

**Activities:**
- 4-3-2 technique (retell story in 4min, then 3min, then 2min)
- Speed reading
- Repeated readings (increasing speed)
- Timed writing
- Shadowing (repeat immediately after hearing)

**Assessment focus:**
- Speed (words per minute)
- Fluidity (reduction in pauses)
- Hesitation markers
- NOT accuracy (you already know this content)

**Example exercises:**
- Retell your morning routine 3x, getting faster each time
- Read familiar text, trying to improve speed
- Shadow a podcast episode you've heard before

### Critical Principle: **Strand Balance**

Nation's research shows optimal learning requires roughly **equal time** across all four strands (≈25% each). Systems that over-focus on one strand (e.g., Duolingo = mostly language-focused learning) produce imbalanced proficiency.

---

## Critique of Current System

### What's Missing

1. **No strand differentiation**: Everything is treated as "practice"
2. **No fluency strand**: Never practice for speed/automaticity
3. **No meaning-input**: No comprehension-only activities
4. **Over-correction**: All errors corrected, appropriate only for language-focused strand
5. **No progression model**: Don't distinguish learning vs. mastery vs. fluency-ready

### What Exists But Isn't Integrated

- ✅ FSRS algorithm implemented (`state/fsrs.py`)
- ✅ SRS server with due items tracking (`mcp_servers/srs_server/`)
- ✅ Quality ratings (0-5) in review_history
- ✅ Mastery database schema
- ❌ But coaching workflow doesn't call SRS server
- ❌ Quality ratings don't feed into scheduling
- ❌ No concept of "mastered" vs. "learning"

---

## Redesigned Architecture

### 1. Knowledge Graph Node Model (Revised)

#### Required Fields (All Nodes)

```yaml
id: constr.es.subjunctive_present
type: Construction
label: Present subjunctive
cefr_level: B1

# NEW: Strand classification (can be multiple)
strands:
  - language_focused    # Primary: explicit grammar study
  - meaning_output      # Secondary: can practice in communication

# Existing fields
prerequisites: [constr.es.present_indicative, morph.es.subjunctive_endings]
can_do: [cando.es.express_doubt_B1, cando.es.express_desire_A2]
diagnostics:
  form: "yo hable, tú hables, él/ella hable..."
  function: "express doubt, desire, emotion, uncertainty"
```

#### Strand-Specific Exercise Metadata

```yaml
# Language-focused exercises (explicit practice)
exercises:
  language_focused:
    - type: "controlled_drill"
      prompt: "Transform: 'Yo creo que viene' → 'Dudo que...'"
      focus: "form_accuracy"
    - type: "error_correction"
      prompt: "Correct: 'Quiero que tú vienes'"

  # Meaning-output exercises (communicative)
  meaning_output:
    - type: "production"
      prompt: "Tell me what you want to happen this weekend"
      focus: "message_communication"
      correction_style: "minimal"  # Only if communication fails

  # Fluency exercises (automaticity with mastered items)
  fluency:
    - type: "speed_drill"
      prompt: "Express 10 desires in 60 seconds using quiero que + subjunctive"
      focus: "speed"
      correction_style: "none"  # Speed over accuracy
```

#### Example: Lexeme Node

```yaml
id: lexeme.es.parecer
type: Lexeme
label: parecer (to seem / to appear)
cefr_level: A2

strands:
  - language_focused    # Learn meanings/forms
  - meaning_input       # Recognize in listening/reading
  - meaning_output      # Use in speech/writing
  - fluency            # Automatize once known

frequency:
  zipf: 5.23
  familiarity: 4.8

exercises:
  language_focused:
    - "Study: parecer + adjective (me parece interesante)"
    - "Study: parecer que + indicative/subjunctive"

  meaning_input:
    - "Listen to opinions, identify when 'parecer' expresses speaker's view"

  meaning_output:
    - "Give your opinion about a movie using 'parecer'"

  fluency:
    - "Express 5 opinions in 30 seconds using parecer"
```

#### Example: Meaning-Input Node

```yaml
id: activity.es.listen_travel_podcast_A2
type: MeaningInputActivity
label: Listen: Travel podcast episode (A2)
cefr_level: A2

strands:
  - meaning_input      # Primary strand

target_nodes:
  - lex.es.viajar
  - lex.es.hotel
  - constr.es.past_tense

material:
  source: "podcast_travel_tales_ep_03.mp3"
  duration: "5min"
  vocabulary_coverage: 98%  # Mostly known words

exercises:
  meaning_input:
    - type: "comprehension_check"
      questions:
        - "¿Adónde viajó el narrador?"
        - "¿Qué problema tuvo en el hotel?"
        - "¿Cómo lo resolvió?"
      assessment: "binary" # understood / didn't understand
```

### 2. Session Planning Algorithm

#### Goals
- Balance four strands (≈25% each)
- Integrate SRS due items
- Mix learning (new) + review (due) + fluency (mastered)
- Respect CEFR level and prerequisites

#### Inputs

```python
# What's available to teach
frontier_nodes = kg.next(learner_id, k=20)  # Prerequisites met, not mastered

# What needs review
due_items = srs.due(learner_id, limit=30)   # Based on FSRS stability

# What's ready for fluency practice
mastered_items = srs.mastered(learner_id, stability_min=21, reps_min=3)

# Learner profile
learner_profile = load_yaml('state/learner.yaml')
# - current_level: A2
# - topics_of_interest: [travel, food, music]
# - session_duration: 20min
```

#### Algorithm (Pseudocode)

```python
def plan_session(learner_id, duration_minutes=20):
    """
    Plan a balanced session across four strands.

    Returns session_plan with exercises from each strand.
    """

    # Target: 25% per strand (5min each for 20min session)
    target_time_per_strand = duration_minutes / 4  # 5 minutes

    # Get available materials
    frontier = kg.next(learner_id, k=20)
    due = srs.due(learner_id, limit=30)
    mastered = srs.mastered(learner_id, stability_min=21, reps_min=3)

    # Filter by strand and prioritize
    session_plan = {
        'meaning_input': [],
        'meaning_output': [],
        'language_focused': [],
        'fluency': []
    }

    # 1. Meaning-focused Input (5 min)
    # Prioritize: comprehensible, interesting, new content
    input_candidates = filter_by_strand(frontier, 'meaning_input')
    input_candidates = filter_by_topics(input_candidates, learner.topics)
    session_plan['meaning_input'] = select_exercises(
        input_candidates,
        target_time=5,
        variety=True  # Mix listening and reading
    )

    # 2. Meaning-focused Output (5 min)
    # Prioritize: communicative tasks, i+1 stretch
    output_candidates = filter_by_strand(frontier + due, 'meaning_output')
    output_candidates = sort_by_communicative_value(output_candidates)
    session_plan['meaning_output'] = select_exercises(
        output_candidates,
        target_time=5,
        mix_new_and_review=True  # 60% review, 40% new
    )

    # 3. Language-focused Learning (5 min)
    # Prioritize: due reviews, then new high-frequency items
    lfl_candidates = filter_by_strand(due + frontier, 'language_focused')
    lfl_candidates = sort_by_priority(
        lfl_candidates,
        prefer_due=True,         # Review before new
        prefer_high_freq=True    # High-freq items first
    )
    session_plan['language_focused'] = select_exercises(
        lfl_candidates,
        target_time=5,
        mix_controlled_and_production=True
    )

    # 4. Fluency Development (5 min)
    # Prioritize: well-mastered items, speed focus
    fluency_candidates = filter_by_strand(mastered, 'fluency')
    fluency_candidates = filter_by_confidence(
        fluency_candidates,
        min_stability=21,    # At least 3 weeks retention
        min_reps=3           # Practiced multiple times
    )
    session_plan['fluency'] = select_exercises(
        fluency_candidates,
        target_time=5,
        focus='speed_and_automaticity'
    )

    return session_plan
```

#### Rebalancing If Materials Scarce

```python
# If not enough mastered items for fluency strand:
if len(session_plan['fluency']) == 0:
    # Redistribute time to other strands
    # Or use repeated readings of meaning-input materials for fluency
    session_plan['fluency'] = create_speed_reading_from_input(
        session_plan['meaning_input']
    )
```

### 3. Assessment Model (Strand-Specific)

#### Meaning-focused Input
**Focus**: Comprehension, not production

**Assessment**:
- Binary: Understood / Didn't understand
- Or: 0-3 scale (didn't understand / partial / mostly / fully understood)
- Comprehension questions (in L1 or L2)

**No quality rating needed** - just track exposure and comprehension

**Tracking**:
```python
log_meaning_input_attempt(
    node_id='activity.es.travel_podcast_A2',
    understood=True,  # boolean
    comprehension_score=2.5,  # 0-3
    timestamp=now()
)

# Update exposure count (not FSRS - this isn't retrieval practice)
increment_exposure_count(node_id)
```

#### Meaning-focused Output
**Focus**: Successful communication

**Assessment**:
- Primary: Was message communicated? (Yes/No)
- Secondary: Quality of communication (0-5)
  - 5: Message clear, natural, effective
  - 4: Message clear with minor issues
  - 3: Message understood but required clarification
  - 2: Message partially understood
  - 1: Message mostly unclear
  - 0: Communication failed

**Correction**: Minimal - only if communication breaks down

**Tracking**:
```python
log_meaning_output_attempt(
    node_id='function.es.restaurant_recommendation',
    communication_successful=True,
    quality=4,  # Good communication
    errors_noted=['article_gender'],  # For tracking, not correction
    timestamp=now()
)

# Update FSRS - this IS retrieval practice
srs.update(item_id, quality=4)
```

#### Language-focused Learning
**Focus**: Accuracy of form

**Assessment**:
- Detailed quality rating (0-5)
  - 5: Perfect form, no errors
  - 4: Minor errors (articles, minor morphology)
  - 3: Noticeable errors but structure recognizable
  - 2: Major errors, structure compromised
  - 1: Severe errors
  - 0: Incorrect or no attempt

**Correction**: Explicit, detailed feedback

**Tracking**:
```python
log_language_focused_attempt(
    node_id='constr.es.subjunctive_present',
    quality=3,  # Adequate but with errors
    errors={
        'type': 'morphology',
        'details': 'used indicative instead of subjunctive'
    },
    correction_given=True,
    timestamp=now()
)

# Update FSRS with quality rating
srs.update(item_id, quality=3)
```

#### Fluency Development
**Focus**: Speed and automaticity

**Assessment**:
- Speed metrics (WPM, time to complete)
- Fluidity (pause count, hesitation markers)
- Improvement over baseline
- Accuracy NOT assessed (already mastered)

**Correction**: None - errors tolerated for speed

**Tracking**:
```python
log_fluency_attempt(
    node_id='constr.es.subjunctive_present',
    duration_seconds=45,
    output_word_count=62,
    words_per_minute=82.6,
    pause_count=3,
    baseline_wpm=65,  # Previous attempt
    improvement_pct=27,
    timestamp=now()
)

# Don't update FSRS difficulty - this is different dimension
# Track fluency progression separately
update_fluency_metrics(node_id, wpm=82.6)
```

### 4. Data Model (Schema Changes)

#### New Tables

```sql
-- Extend items table with strand metadata
ALTER TABLE items ADD COLUMN primary_strand TEXT;
-- Values: 'meaning_input', 'meaning_output', 'language_focused', 'fluency'

-- Track mastery status
ALTER TABLE items ADD COLUMN mastery_status TEXT DEFAULT 'learning';
-- Values: 'new', 'learning', 'mastered', 'fluency_ready'

ALTER TABLE items ADD COLUMN last_mastery_check TIMESTAMP;

-- Create fluency_metrics table
CREATE TABLE fluency_metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT NOT NULL,
    session_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_seconds REAL NOT NULL,
    output_word_count INTEGER,
    words_per_minute REAL,
    pause_count INTEGER,
    hesitation_markers INTEGER,
    baseline_wpm REAL,  -- Previous best
    improvement_pct REAL,
    notes TEXT,
    FOREIGN KEY (item_id) REFERENCES items(item_id) ON DELETE CASCADE
);

CREATE INDEX idx_fluency_item_date ON fluency_metrics(item_id, session_date);

-- Create meaning_input_log table (exposure tracking)
CREATE TABLE meaning_input_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id TEXT NOT NULL,
    session_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    understood BOOLEAN,
    comprehension_score REAL,  -- 0-3 scale
    material_id TEXT,  -- e.g., podcast episode
    notes TEXT
);

CREATE INDEX idx_input_log_node ON meaning_input_log(node_id);

-- Create meaning_output_log table
CREATE TABLE meaning_output_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id TEXT NOT NULL,
    session_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    communication_successful BOOLEAN,
    quality INTEGER,  -- 0-5
    errors_noted TEXT,  -- JSON array of error types
    required_clarification BOOLEAN,
    notes TEXT
);

CREATE INDEX idx_output_log_node ON meaning_output_log(node_id);

-- Extend review_history with strand context
ALTER TABLE review_history ADD COLUMN strand TEXT;
ALTER TABLE review_history ADD COLUMN exercise_type TEXT;
```

#### Views for Session Planning

```sql
-- View: Mastered items ready for fluency practice
CREATE VIEW fluency_ready_items AS
SELECT
    i.item_id,
    i.node_id,
    i.stability,
    i.reps,
    i.difficulty,
    i.last_review
FROM items i
WHERE
    i.stability >= 21.0      -- At least 3 weeks retention
    AND i.reps >= 3          -- Practiced multiple times
    AND i.mastery_status = 'mastered'
ORDER BY i.last_review ASC;

-- View: Items in learning phase
CREATE VIEW learning_items AS
SELECT
    i.item_id,
    i.node_id,
    i.stability,
    i.reps,
    i.difficulty
FROM items i
WHERE
    i.mastery_status IN ('new', 'learning')
    AND (i.reps < 3 OR i.stability < 21.0);

-- View: Session balance metrics
CREATE VIEW strand_balance_last_10_sessions AS
SELECT
    DATE(session_date) as session_day,
    strand,
    COUNT(*) as exercise_count,
    SUM(duration_seconds) as total_seconds
FROM (
    SELECT session_date, strand, 60 as duration_seconds
    FROM review_history
    WHERE strand IS NOT NULL
    UNION ALL
    SELECT session_date, 'fluency', duration_seconds
    FROM fluency_metrics
    UNION ALL
    SELECT session_date, 'meaning_input', 120 as duration_seconds
    FROM meaning_input_log
)
WHERE session_date >= datetime('now', '-10 days')
GROUP BY session_day, strand;
```

### 5. Progression Model (Mastery Thresholds)

#### States

```
NEW → LEARNING → MASTERED → FLUENCY_READY
```

#### Transitions

**NEW → LEARNING**
- Trigger: First attempt logged
- Action: Create item in SRS with default parameters

**LEARNING → MASTERED**
- Criteria:
  - `reps >= 3` (practiced at least 3 times)
  - `stability >= 21.0` (3-week retention)
  - `avg_quality >= 3.5` (consistently adequate or better)
- Action:
  - Set `mastery_status = 'mastered'`
  - Make available for fluency strand
  - Reduce review frequency (rely on FSRS)

**MASTERED → FLUENCY_READY**
- Criteria:
  - Already mastered
  - Appears in multiple strands (e.g., can be used in meaning-output)
- Action:
  - Add to fluency exercise pool
  - Track speed/automaticity metrics

#### Regression Handling

If mastered item shows quality decline:
```python
if item.mastery_status == 'mastered' and quality < 3:
    # Regression detected
    item.mastery_status = 'learning'
    log_regression(item_id, quality)
    # Item returns to regular review cycle
```

### 6. Self-Assessment for Fluency

Since fluency practice emphasizes speed and may not have automatic measurement, learners assess their own performance.

#### Self-Assessment UI (Conceptual)

After fluency exercise:
```
How did you do? (Focus on SPEED and FLUENCY, not accuracy)

Hesitation:
  [ ] Smooth, minimal pauses
  [ ] Some pauses but kept going
  [ ] Frequent pauses, lots of hesitation

Speed:
  [ ] Fast, automatic
  [ ] Moderate pace
  [ ] Slow, had to think

Confidence:
  [ ] Felt easy, in my comfort zone
  [ ] Required some effort
  [ ] Very challenging

[Optional] Time yourself: [__:__] (minutes:seconds)
[Optional] Word count: [____]
```

Self-assessment logged as:
```python
log_fluency_self_assessment(
    item_id='constr.es.subjunctive_present',
    smoothness='minimal_pauses',
    speed='moderate',
    confidence='easy',
    self_timed_seconds=48,
    estimated_word_count=55
)
```

#### Integration with Objective Metrics

When speech recognition available:
- Compare self-assessment with actual WPM
- Calibrate learner's self-perception
- Use as training for accurate self-monitoring

### 7. Revised Coaching Workflow

#### Updated SPANISH_COACH.md (Summary)

```
## Session Start

1. Call session planner (includes SRS integration):

   session = plan_balanced_session(learner_id='brett', duration=20)

   Returns:
   {
     'meaning_input': [listen_podcast_travel, read_article_food],
     'meaning_output': [describe_weekend, role_play_restaurant],
     'language_focused': [subjunctive_drill, preterite_practice],
     'fluency': [speed_retell_story, rapid_opinion_giving]
   }

2. Present session plan to learner:
   "Today's 20-minute session:
   - Listening: Travel podcast (5 min)
   - Speaking: Describe your weekend plans (5 min)
   - Grammar: Subjunctive practice (5 min)
   - Fluency: Rapid-fire opinions (5 min)"

## Conduct Each Strand

### Meaning-Input Exercise
- Present material (audio/text)
- Ask comprehension questions
- No correction of learner production
- Log: understood (true/false), comprehension_score (0-3)

### Meaning-Output Exercise
- Set communicative task
- Learner produces (speech/writing)
- Assess: message communicated? (yes/no)
- Minimal correction (only if communication fails)
- Log: communication_successful, quality (0-5), errors_noted
- Update SRS: srs.update(item_id, quality)

### Language-Focused Exercise
- Explicit practice of target form
- Learner produces
- Assess: quality (0-5), detailed error analysis
- Explicit correction with explanation
- Log: quality, errors, correction_given
- Update SRS: srs.update(item_id, quality)

### Fluency Exercise
- Timed/speed-focused task using MASTERED content
- Learner produces rapidly
- Assess: speed (WPM), fluidity, improvement
- NO correction (errors tolerated)
- Self-assessment prompt
- Log: fluency_metrics (duration, wpm, pause_count)

## Session End

- Summarize progress
- Note what moved to 'mastered' status
- Preview next session strand balance
```

---

## Implementation Roadmap

### Phase 1: Data Model (Week 1)
- [ ] Create migration script for schema changes
- [ ] Add strand field to all KG nodes
- [ ] Create fluency_metrics table
- [ ] Create meaning_input_log table
- [ ] Create meaning_output_log table
- [ ] Update review_history with strand context
- [ ] Create views (fluency_ready_items, learning_items, etc.)

### Phase 2: Session Planner (Week 2)
- [ ] Implement `plan_balanced_session()` function
- [ ] Implement strand filtering logic
- [ ] Implement mastery status transitions
- [ ] Create `srs.mastered()` endpoint
- [ ] Test session planning with various learner profiles

### Phase 3: Assessment Logic (Week 2-3)
- [ ] Implement strand-specific assessment functions
- [ ] Create logging functions per strand
- [ ] Implement fluency self-assessment UI
- [ ] Update SRS integration (quality → FSRS)

### Phase 4: Content Tagging (Week 3-4)
- [ ] Review all 25 existing KG nodes
- [ ] Tag each with appropriate strand(s)
- [ ] Create strand-specific exercises for each node
- [ ] Create meaning-input activities (listening, reading)
- [ ] Create fluency exercises for high-frequency items

### Phase 5: Coaching Integration (Week 4)
- [ ] Rewrite SPANISH_COACH.md with strand workflow
- [ ] Update MCP server calls to include strand context
- [ ] Test end-to-end session with all four strands
- [ ] Gather feedback and iterate

### Phase 6: Measurement & Tuning (Ongoing)
- [ ] Track strand balance over time (view: strand_balance_last_10_sessions)
- [ ] Monitor mastery progression rates
- [ ] Calibrate fluency self-assessment against objective metrics
- [ ] Adjust FSRS parameters based on real data

---

## Open Questions & Design Decisions Needed

### 1. Strand Balance Flexibility ✅ DECIDED
**Question**: Strict 25% per strand, or dynamic based on learner needs?

**Decision**: Flexible with increasing pressure to rebalance

**Implementation**:
```python
# Target: 25% per strand, tolerance: ±5 percentage points
# Pressure increases proportionally with imbalance

def calculate_strand_weights(recent_session_history, learner_preference=None):
    """
    Calculate weights for next session based on recent balance.

    Returns higher weights for under-practiced strands.
    Pressure increases with distance from 25% target.
    """
    # Get last 10 sessions' strand distribution
    actual_distribution = get_strand_percentages(last_n_sessions=10)

    target = 0.25  # 25% per strand
    weights = {}

    for strand in ['meaning_input', 'meaning_output', 'language_focused', 'fluency']:
        actual = actual_distribution[strand]
        deviation = target - actual

        # Pressure increases non-linearly with deviation
        if abs(deviation) <= 0.05:  # Within tolerance (20-30%)
            weights[strand] = 1.0  # Neutral
        elif abs(deviation) <= 0.10:  # Moderate imbalance (15-20% or 30-35%)
            weights[strand] = 1.0 + (deviation * 2)  # Gentle pressure
        else:  # Severe imbalance (<15% or >35%)
            weights[strand] = 1.0 + (deviation * 4)  # Strong pressure

    # Learner can override (defeasible)
    if learner_preference:
        # e.g., learner_preference = {'meaning_output': 0.4, 'fluency': 0.1}
        # System suggests rebalancing but respects learner choice
        weights = apply_learner_override(weights, learner_preference)

    return normalize_weights(weights)
```

**Example**:
- Last 10 sessions: Input 15%, Output 35%, Language 30%, Fluency 20%
- Output is over (35% vs 25% = +10%), Input is under (15% vs 25% = -10%)
- Next session: Input gets strong boost, Output gets de-emphasized
- But if learner says "I want to practice speaking today", system allows it

**Rationale**:
- Nation emphasizes balance but not rigidity
- Learner autonomy is important (defeasibility)
- Self-correcting system prevents long-term drift
- ±5% tolerance prevents over-fitting to exact percentages

### 2. Mastery Threshold Values ✅ DECIDED
**Question**: What counts as "mastered"?

**Decision**: Reasonable defaults based on FSRS data, learner-adjustable

**Default Thresholds**:
```python
MASTERY_CRITERIA = {
    'default': {
        'stability_days': 21,      # 3-week retention
        'min_reps': 3,              # At least 3 successful retrievals
        'avg_quality': 3.5,         # Consistently adequate or better
    },
    'conservative': {
        'stability_days': 30,       # 1-month retention
        'min_reps': 5,
        'avg_quality': 4.0,
    },
    'aggressive': {
        'stability_days': 14,       # 2-week retention
        'min_reps': 2,
        'avg_quality': 3.0,
    }
}

# Learner can adjust in learner.yaml:
# mastery_preference: 'default'  # or 'conservative' or 'aggressive'
# Or custom: {stability_days: 25, min_reps: 4, avg_quality: 3.8}
```

**Nation's Approach**:
- Doesn't obsess over exact thresholds
- Values "sufficient practice" over "perfect mastery"
- Trusts natural recycling through strands
- If you can use it in meaning-output, it's mastered enough

**Implementation Philosophy**:
- System uses defaults silently (learner doesn't need to think about it)
- If learner feels items are moving to fluency too fast/slow, they can adjust
- Provide feedback: "This item moved to fluency practice because you've used it successfully 3 times over 3 weeks"
- Let learners observe and calibrate their preferences

**Rationale**:
- Research-informed defaults (FSRS optimal parameters)
- Respects individual variation (some learners need more/less practice)
- Transparent (learner can understand why something is "mastered")
- Adjustable without being burdensome

### 3. Fluency Measurement ✅ DECIDED
**Question**: How to objectively measure fluency without speech recognition?

**Decision**: Multi-method approach using what's practical in CLI

**Methods (in priority order)**:

**1. Self-Timing (Nation's preferred method)**
```
Fluency Exercise: Retell your morning routine

[Timer starts]
You speak/type...
[Timer ends]

How many words/utterances? [___]
Duration: 1:23 (83 seconds)
→ Estimated WPM: ~43

Improvement from last time (38 WPM): +13%
```

**What Nation Uses**:
- 4-3-2 technique: Tell story in 4min, then 3min, then 2min
- Simple stopwatch, learner self-times
- Improvement over iterations is the metric (not absolute WPM)
- **Learner perception of getting faster is valuable data**

**2. Subjective Feel (Nation validates this)**
```
How did that feel?
[ ] Smooth and automatic
[ ] Some hesitation but manageable
[ ] Struggled, lots of pauses

Compared to last time:
[ ] Easier/faster
[ ] About the same
[ ] Harder/slower
```

**3. Objective Metrics (when available)**
- CLI can count words if text-based
- Speech recognition can measure actual WPM + pause duration
- But DON'T wait for perfect measurement to start fluency practice

**Implementation**:
```python
def conduct_fluency_exercise(node_id, exercise):
    """Conduct fluency exercise with pragmatic measurement."""

    # Present task
    print(f"Fluency practice: {exercise.prompt}")
    print("Goal: Speed and smoothness, not accuracy")
    print("\nPress ENTER when ready to start...")
    input()

    # Start timer
    start_time = time.time()
    print("GO! (Press ENTER when done)")

    # Learner produces (typing or speaking aloud)
    output = input() if exercise.mode == 'text' else wait_for_enter()

    # End timer
    duration = time.time() - start_time

    # Count words (if text-based)
    word_count = len(output.split()) if output else None

    # Self-assessment
    smoothness = prompt_choice("How smooth?", ["Automatic", "Some pauses", "Struggled"])
    feel = prompt_choice("Compared to last time?", ["Easier", "Same", "Harder"])

    # Calculate metrics
    wpm = (word_count / duration) * 60 if word_count else None

    # Log
    log_fluency_attempt(
        node_id=node_id,
        duration_seconds=duration,
        word_count=word_count,
        words_per_minute=wpm,
        smoothness=smoothness,
        improvement_feel=feel,
        timestamp=now()
    )

    # Feedback
    baseline = get_baseline_wpm(node_id)
    if wpm and baseline:
        improvement = ((wpm - baseline) / baseline) * 100
        print(f"\nYour pace: {wpm:.0f} WPM ({improvement:+.0f}% from baseline)")
    else:
        print(f"\nCompleted in {duration:.0f} seconds. Keep practicing!")
```

**What We Measure**:
- **Always**: Duration, subjective smoothness, perceived improvement
- **When possible**: Word count, calculated WPM
- **Never**: Accuracy (that's not the point of fluency practice)

**Nation's Philosophy**:
- Large amounts of easy practice > precise measurement
- Learner awareness of speed is training self-monitoring skill
- Improvement over time matters, not absolute values
- Simple tools work fine (stopwatch beats complex systems)

**Rationale**:
- CLI-compatible (works with typing OR speaking aloud)
- Learner feelings are valid data (Nation confirms this)
- Objective metrics when available, but don't block on them
- Focus on practice volume, not measurement perfection

### 4. Input Strand Content
**Question**: Where does meaning-input content come from?

**Options**:
- A) Curated library of graded materials (podcasts, articles, videos)
- B) Links to external resources (YouTube, podcasts, news sites)
- C) Generated materials (LLM creates graded reading passages)
- D) User-uploaded materials

**Recommendation**: Start with (B) links, add (C) generation for customization

### 5. Session Interruption
**Question**: What if learner needs to stop mid-session?

**Design**:
- Save session state
- Allow resuming at strand boundary
- Don't penalize incomplete sessions
- Track "completed strands" separately from "attempted strands"

### 6. Review Scheduling Across Strands
**Question**: If I've mastered subjunctive in language-focused strand, does it automatically appear in all strands?

**Proposal**:
- Item tagged with multiple strands appears in review queue for each
- Each strand tracked separately in review_history
- Mastery is PER STRAND (mastered for language-focused, but still learning for meaning-output)

**Alternate**:
- Single mastery status applies across strands
- Once mastered anywhere, available everywhere

**Needs decision**: Separate or unified mastery?

### 7. Correction Across Strands
**Question**: What if learner makes error in meaning-output strand?

**Proposed guideline**:
- Meaning-input: No production, no correction
- Meaning-output: Note error, don't correct unless communication fails
- Language-focused: Correct explicitly
- Fluency: Don't correct (tolerate errors for speed)

**Edge case**: If learner makes same error repeatedly across meaning-output exercises, do we eventually flag it for language-focused practice?

**Recommendation**: Yes - error tracking across strands feeds into language-focused selection

---

## Testing Strategy

### Unit Tests
- [ ] Strand filtering logic
- [ ] Mastery status transitions
- [ ] Session planning algorithm (strand balance)
- [ ] Quality assessment per strand
- [ ] FSRS integration with quality ratings

### Integration Tests
- [ ] End-to-end session flow
- [ ] SRS + KG + strand integration
- [ ] Logging to all new tables
- [ ] View queries (fluency_ready_items, etc.)

### User Testing (with Brett)
- [ ] Run 5 sessions with full strand balance
- [ ] Self-assess fluency exercises
- [ ] Evaluate if 25% per strand feels right
- [ ] Check if mastery thresholds make sense
- [ ] Gather subjective feedback on progression

---

## Success Metrics

After redesign implementation, measure:

1. **Strand Balance**: % of time spent in each strand over 10 sessions
   - Target: 25% ± 5% per strand

2. **Progression Rate**: Days from NEW → MASTERED
   - Track: avg days, distribution

3. **Review Burden**: % of session time spent on reviews vs. new content
   - Target: 60% review, 40% new (Nation's guideline)

4. **Fluency Improvement**: WPM or smoothness ratings over time
   - Track: improvement slope per item

5. **Mastery Retention**: Do "mastered" items stay mastered?
   - Regression rate: should be < 10%

6. **Subjective**: Does learner feel balanced exposure?
   - Weekly self-report on four strands

---

## References

### Nation's Four Strands
- Nation, I.S.P. (2007). *The Four Strands*. Innovation in Language Learning and Teaching, 1(1), 2-13.
- Nation, I.S.P. (2013). *Learning Vocabulary in Another Language* (2nd ed.). Cambridge University Press.

### FSRS Algorithm
- https://github.com/open-spaced-repetition/fsrs4anki
- Ye et al. (2024). *Optimizing Spaced Repetition Schedule by Capturing the Dynamics of Memory*

### Task-Based Language Teaching
- Ellis, R. (2003). *Task-based Language Learning and Teaching*. Oxford University Press.

### Fluency Development
- Nation, P. & Newton, J. (2009). *Teaching ESL/EFL Listening and Speaking*. Routledge.
- 4-3-2 Technique: Maurice (1983)

---

## Appendix A: Example Redesigned Nodes

### Construction (Multi-Strand)

```yaml
id: constr.es.subjunctive_present
type: Construction
label: Present subjunctive
cefr_level: B1

strands:
  - language_focused    # Primary: explicit study
  - meaning_output      # Use in communication
  - fluency            # Automatize once mastered

prerequisites:
  - constr.es.present_indicative
  - morph.es.subjunctive_endings

diagnostics:
  form: "yo hable, tú hables, él/ella hable..."
  function: "Express doubt, desire, emotion, uncertainty"
  usage_constraints: "After specific triggers (querer que, dudar que, etc.)"

# Strand-specific exercises
exercises:
  language_focused:
    - type: "controlled_drill"
      prompt: "Transform: 'Yo creo que viene' → 'Dudo que...'"
      expected: "Dudo que venga"
      assessment: "quality_0_5"
      correction: "explicit"

    - type: "error_correction"
      prompt: "Correct: 'Quiero que tú vienes mañana'"
      expected: "Quiero que tú vengas mañana"

  meaning_output:
    - type: "production"
      prompt: "Tell me what you hope will happen this weekend"
      assessment: "communication_success"
      correction: "minimal"

    - type: "role_play"
      prompt: "You're planning a trip. Express your desires and concerns."

  fluency:
    - type: "speed_production"
      prompt: "Express 10 desires in 60 seconds using 'quiero que + subjunctive'"
      assessment: "wpm_and_fluidity"
      correction: "none"
      baseline_wpm: 45  # Target for this level

    - type: "4_3_2"
      prompt: "Describe your ideal vacation (4min, then 3min, then 2min)"
      assessment: "improvement_over_iterations"
```

### Meaning-Input Activity

```yaml
id: activity.es.podcast_travel_madrid_A2
type: MeaningInputActivity
label: "Podcast: Traveling to Madrid (A2)"
cefr_level: A2

strands:
  - meaning_input

material:
  source: "https://example.com/podcast/travel_madrid.mp3"
  duration: "4min 30sec"
  transcript_available: true
  vocabulary_coverage: 98%  # i+1 level
  topics: [travel, transportation, tourism]

target_nodes:
  - lex.es.viajar
  - lex.es.transporte
  - constr.es.preterite_simple

exercises:
  meaning_input:
    - type: "comprehension_check"
      questions:
        - "¿Adónde viajó el narrador?"
        - "¿Qué tipo de transporte usó?"
        - "¿Qué lugares visitó en Madrid?"
      assessment: "comprehension_0_3"
      correction: "none"

    - type: "follow_up_discussion"
      prompt: "Have you been to Madrid? Would you like to go?"
      assessment: "engagement"

notes: |
  This is pure input - no production pressure.
  Focus on understanding, not speaking.
  Can listen multiple times.
```

### Lexeme (All Strands)

```yaml
id: lexeme.es.parecer
type: Lexeme
label: "parecer (to seem, to think/appear)"
cefr_level: A2

strands:
  - language_focused
  - meaning_input
  - meaning_output
  - fluency

frequency:
  zipf: 5.23
  familiarity: 4.8
  corpus: "Corpus del Español"

forms:
  - infinitive: "parecer"
  - present_1s: "parezco"
  - present_3s: "parece"
  - impersonal: "me parece"

collocations:
  - "me parece que..."
  - "me parece bien/mal"
  - "parece mentira"

exercises:
  language_focused:
    - type: "form_study"
      prompt: "Study: parecer + adjective → me parece interesante"

    - type: "collocation_drill"
      prompt: "Complete: Me _____ que es una buena idea"

  meaning_input:
    - type: "recognition"
      prompt: "Listen to opinions. When does 'parecer' express the speaker's view?"
      material: "opinion_podcast_a2.mp3"

  meaning_output:
    - type: "opinion_expression"
      prompt: "What do you think about [topic]? Use 'me parece'"

  fluency:
    - type: "rapid_opinions"
      prompt: "Give your opinion on 5 topics in 60 seconds using 'me parece'"
      baseline_wpm: 40
```

---

## Appendix B: Sample Session Plan Output

```json
{
  "learner_id": "brett",
  "session_date": "2025-11-05T14:00:00",
  "duration_target_minutes": 20,
  "strand_balance": {
    "meaning_input": 5,
    "meaning_output": 5,
    "language_focused": 5,
    "fluency": 5
  },
  "exercises": [
    {
      "strand": "meaning_input",
      "node_id": "activity.es.podcast_travel_madrid_A2",
      "type": "listening_comprehension",
      "duration_estimate_min": 5,
      "instructions": "Listen to podcast about Madrid travel",
      "assessment_type": "comprehension_0_3"
    },
    {
      "strand": "meaning_output",
      "node_id": "function.es.describe_plans",
      "type": "production",
      "duration_estimate_min": 5,
      "instructions": "Describe your weekend plans",
      "assessment_type": "communication_success",
      "item_id": "item_brett_describe_plans_01",
      "due_status": "review",
      "last_practiced": "2025-11-03",
      "current_stability": 3.2
    },
    {
      "strand": "language_focused",
      "node_id": "constr.es.subjunctive_present",
      "type": "controlled_drill",
      "duration_estimate_min": 5,
      "instructions": "Practice subjunctive transformations",
      "assessment_type": "quality_0_5",
      "item_id": "item_brett_subjunctive_01",
      "due_status": "review",
      "last_practiced": "2025-11-02",
      "current_stability": 4.5
    },
    {
      "strand": "fluency",
      "node_id": "constr.es.present_indicative",
      "type": "speed_production",
      "duration_estimate_min": 5,
      "instructions": "Describe your daily routine in 90 seconds (aim for 60 words)",
      "assessment_type": "wpm_and_fluidity",
      "item_id": "item_brett_present_indicative_02",
      "mastery_status": "mastered",
      "baseline_wpm": 42
    }
  ],
  "balance_status": "balanced",
  "notes": "Good mix of review (2) and input (1) with fluency practice on mastered content"
}
```

---

**END OF REDESIGN DOCUMENT**

Status: Ready for review and critique
