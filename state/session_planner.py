"""
Session Planning for Four Strands Language Learning

Implements balanced session planning across Nation's Four Strands:
- Meaning-focused Input (comprehension)
- Meaning-focused Output (communication)
- Language-focused Learning (explicit study)
- Fluency Development (automaticity)

Reference: FOUR_STRANDS_REDESIGN.md
"""

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import yaml

# Target strand distribution (Nation's recommendation)
TARGET_STRAND_PERCENTAGE = 0.25  # 25% per strand
TOLERANCE_PERCENTAGE = 0.05      # ±5% tolerance (20-30% acceptable)

# Mastery criteria (default settings)
DEFAULT_MASTERY_CRITERIA = {
    "stability_days": 21,
    "min_reps": 3,
    "avg_quality": 3.5
}

# CEFR level ordering (for i-1 filtering)
CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]


def cefr_to_numeric(level: str) -> int:
    """Convert CEFR level to numeric value for comparison."""
    try:
        return CEFR_LEVELS.index(level)
    except ValueError:
        return 0  # Default to A1 if unknown


def infer_strand_from_node_type(node_type: str) -> str:
    """
    Infer primary strand from node type.

    Following Nation's Four Strands framework:
    - Lexeme, Construction, Morph → language_focused (explicit study)
    - CanDo, Function, DiscourseMove, AssessmentCriterion → meaning_output (communication)
    - Topic → meaning_input (comprehension)

    Args:
        node_type: Type of KG node

    Returns:
        Strand name: 'meaning_input', 'meaning_output', 'language_focused', or 'fluency'
    """
    if node_type in ["Lexeme", "Construction", "Morph"]:
        return "language_focused"
    elif node_type in ["CanDo", "Function", "DiscourseMove", "PragmaticCue", "AssessmentCriterion"]:
        return "meaning_output"
    elif node_type == "Topic":
        return "meaning_input"
    else:
        return "meaning_output"  # Default fallback


def load_learner_profile(learner_id: str = None) -> dict | None:
    """Load learner profile from state/learner.yaml."""
    profile_path = Path("state/learner.yaml")
    if not profile_path.exists():
        return None

    with open(profile_path) as f:
        profile = yaml.safe_load(f)

    # Return profile if learner_id matches or None (for compatibility)
    if learner_id is None or profile.get("learner_id") == learner_id:
        return profile
    return None


def get_secure_level(learner_id: str, skill: str) -> str:
    """Get secure level for a skill (for i-1 fluency filtering)."""
    profile = load_learner_profile(learner_id)
    if not profile:
        return "A1"  # Conservative default

    # Get from proficiency dict, fall back to A1
    proficiency = profile.get("proficiency", {})
    skill_prof = proficiency.get(skill, {})
    return skill_prof.get("secure_level", "A1")


@dataclass
class StrandBalance:
    """Current strand balance over recent sessions."""
    meaning_input: float      # Percentage (0.0-1.0)
    meaning_output: float
    language_focused: float
    fluency: float
    total_exercises: int
    total_seconds: float

    def get_percentage(self, strand: str) -> float:
        """Get percentage for a specific strand."""
        return getattr(self, strand)

    def deviation_from_target(self, strand: str) -> float:
        """Calculate deviation from 25% target."""
        return TARGET_STRAND_PERCENTAGE - self.get_percentage(strand)


@dataclass
class Exercise:
    """Represents a planned exercise."""
    strand: str
    node_id: str
    item_id: str | None  # May be None for meaning-input activities
    exercise_type: str
    duration_estimate_min: int
    priority_score: float
    instructions: str
    metadata: dict


@dataclass
class SessionPlan:
    """Complete session plan with balanced exercises."""
    learner_id: str
    session_date: datetime
    duration_target_minutes: int
    exercises: list[Exercise]
    strand_balance: StrandBalance
    balance_status: str  # 'balanced', 'slight_imbalance', 'severe_imbalance'
    notes: str


class SessionPlanner:
    """Plans balanced language learning sessions across four strands."""

    def __init__(
        self,
        kg_db_path: Path,
        mastery_db_path: Path,
        mastery_criteria: dict | None = None
    ):
        """
        Initialize session planner.

        Args:
            kg_db_path: Path to knowledge graph database
            mastery_db_path: Path to mastery database
            mastery_criteria: Custom mastery thresholds (optional)
        """
        self.kg_db_path = kg_db_path
        self.mastery_db_path = mastery_db_path
        self.mastery_criteria = mastery_criteria or DEFAULT_MASTERY_CRITERIA

    def get_strand_balance(self, learner_id: str, last_n_sessions: int = 10) -> StrandBalance:
        """
        Get strand balance over recent sessions.

        Args:
            learner_id: Learner identifier
            last_n_sessions: Number of recent sessions to analyze

        Returns:
            StrandBalance with percentage distribution
        """
        conn = sqlite3.connect(self.mastery_db_path)
        cursor = conn.cursor()

        # Query strand_balance_summary view
        cursor.execute("""
            SELECT
                strand,
                total_seconds
            FROM strand_balance_recent
            WHERE session_day >= DATE('now', '-' || ? || ' days')
        """, (last_n_sessions,))

        results = cursor.fetchall()
        conn.close()

        # Calculate totals
        strand_seconds = {
            "meaning_input": 0,
            "meaning_output": 0,
            "language_focused": 0,
            "fluency": 0
        }

        total_seconds = 0
        for strand, seconds in results:
            if strand in strand_seconds:
                strand_seconds[strand] += seconds
                total_seconds += seconds

        # Calculate percentages
        if total_seconds == 0:
            # No recent practice, return equal distribution
            return StrandBalance(
                meaning_input=0.25,
                meaning_output=0.25,
                language_focused=0.25,
                fluency=0.25,
                total_exercises=0,
                total_seconds=0
            )

        return StrandBalance(
            meaning_input=strand_seconds["meaning_input"] / total_seconds,
            meaning_output=strand_seconds["meaning_output"] / total_seconds,
            language_focused=strand_seconds["language_focused"] / total_seconds,
            fluency=strand_seconds["fluency"] / total_seconds,
            total_exercises=len(results),
            total_seconds=total_seconds
        )

    def calculate_strand_weights(
        self,
        balance: StrandBalance,
        learner_preference: dict[str, float] | None = None
    ) -> dict[str, float]:
        """
        Calculate weights for strand selection based on recent balance.

        Implements progressive pressure to rebalance:
        - Within ±5%: Neutral weight (1.0)
        - ±5-10%: Gentle pressure (2x deviation)
        - >10%: Strong pressure (4x deviation)

        Args:
            balance: Current strand balance
            learner_preference: Optional learner override (defeasible)

        Returns:
            Dictionary of weights per strand
        """
        strands = ["meaning_input", "meaning_output", "language_focused", "fluency"]
        weights = {}

        for strand in strands:
            deviation = balance.deviation_from_target(strand)

            # Calculate pressure based on deviation magnitude
            abs_deviation = abs(deviation)

            if abs_deviation <= TOLERANCE_PERCENTAGE:
                # Within tolerance (20-30%)
                weights[strand] = 1.0
            elif abs_deviation <= 0.10:
                # Moderate imbalance (15-20% or 30-35%)
                weights[strand] = 1.0 + (deviation * 2)
            else:
                # Severe imbalance (<15% or >35%)
                weights[strand] = 1.0 + (deviation * 4)

        # Apply learner preference (defeasible)
        if learner_preference:
            for strand, user_weight in learner_preference.items():
                if strand in weights:
                    # Blend system weight with learner preference
                    # System gets 70% weight, learner gets 30%
                    weights[strand] = weights[strand] * 0.7 + user_weight * 0.3

        # Normalize weights to sum to 4.0 (one per strand)
        total = sum(weights.values())
        normalized = {k: (v / total) * 4.0 for k, v in weights.items()}

        return normalized

    def get_frontier_nodes(self, learner_id: str, limit: int = 20) -> list[dict]:
        """
        Get frontier nodes from knowledge graph (prerequisites satisfied).

        Frontier nodes are items that:
        1. Are at or below learner's current CEFR level
        2. Are not yet learned (no item, or item with status='new')
        3. Have all prerequisites satisfied (prerequisites have items with status != 'new')

        Args:
            learner_id: Learner identifier
            limit: Maximum nodes to return

        Returns:
            List of node dictionaries with strand metadata:
            [{"node_id": "...", "type": "...", "label": "...", "cefr_level": "...",
              "primary_strand": "...", "has_prerequisites": bool}]
        """
        # Load learner profile to get current CEFR level
        profile = load_learner_profile(learner_id)
        if not profile:
            return []

        current_level = profile.get("current_level", "A2")
        current_numeric = cefr_to_numeric(current_level)

        # Connect to both KG and mastery databases
        kg_conn = sqlite3.connect(self.kg_db_path)
        kg_conn.row_factory = sqlite3.Row
        kg_conn.execute(f'ATTACH DATABASE "{self.mastery_db_path}" AS mastery')

        try:
            # Step 1: Find candidate nodes (at/below CEFR, not yet learned)
            cursor = kg_conn.cursor()
            cursor.execute('''
                SELECT
                    n.node_id,
                    n.type,
                    n.label,
                    n.cefr_level,
                    n.data_json,
                    i.mastery_status
                FROM nodes n
                LEFT JOIN mastery.items i ON n.node_id = i.node_id
                WHERE n.cefr_level IS NOT NULL
                  AND (i.item_id IS NULL OR i.mastery_status = 'new')
            ''')

            candidates = []
            for row in cursor.fetchall():
                node = dict(row)
                node_cefr_numeric = cefr_to_numeric(node["cefr_level"])

                # Filter by CEFR level
                if node_cefr_numeric <= current_numeric:
                    candidates.append(node)

            # Step 2: Check prerequisites for each candidate
            frontier_nodes = []
            for node in candidates:
                node_id = node["node_id"]

                # Get prerequisites for this node
                cursor.execute('''
                    SELECT e.source_id, i.mastery_status
                    FROM edges e
                    LEFT JOIN mastery.items i ON e.source_id = i.node_id
                    WHERE e.target_id = ? AND e.edge_type = 'prerequisite_of'
                ''', (node_id,))

                prerequisites = cursor.fetchall()
                has_prerequisites = len(prerequisites) > 0

                # Check if all prerequisites are satisfied
                all_satisfied = True
                if has_prerequisites:
                    for prereq in prerequisites:
                        prereq_status = prereq["mastery_status"]
                        # Prerequisite must exist and not be 'new'
                        if prereq_status is None or prereq_status == "new":
                            all_satisfied = False
                            break

                # If all prerequisites satisfied (or no prerequisites), add to frontier
                if all_satisfied:
                    # Parse data_json for primary_strand (may not exist in KG)
                    data = json.loads(node["data_json"])
                    primary_strand = data.get("primary_strand")

                    # If not in data_json, infer from node type
                    if primary_strand is None:
                        primary_strand = infer_strand_from_node_type(node["type"])

                    frontier_nodes.append({
                        "node_id": node["node_id"],
                        "type": node["type"],
                        "label": node["label"],
                        "cefr_level": node["cefr_level"],
                        "primary_strand": primary_strand,
                        "has_prerequisites": has_prerequisites
                    })

            # Step 3: Prioritize nodes with no prerequisites, then by CEFR level
            frontier_nodes.sort(key=lambda x: (
                1 if x["has_prerequisites"] else 0,  # No prereqs first
                cefr_to_numeric(x["cefr_level"]),    # Then lower CEFR
                x["node_id"]                          # Then alphabetically
            ))

            return frontier_nodes[:limit]

        finally:
            kg_conn.close()

    def get_due_items(self, learner_id: str, limit: int = 30) -> list[dict]:
        """
        Get items due for review from SRS.

        Args:
            learner_id: Learner identifier
            limit: Maximum items to return

        Returns:
            List of due items with FSRS metadata
        """
        conn = sqlite3.connect(self.mastery_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Query items table directly (due_items view doesn't include new columns)
        cursor.execute("""
            SELECT
                item_id,
                node_id,
                type,
                last_review,
                stability,
                difficulty,
                reps,
                mastery_status,
                primary_strand
            FROM items
            WHERE (
                last_review IS NULL
                OR julianday('now') - julianday(last_review) >= stability
            )
            ORDER BY last_review ASC NULLS FIRST
            LIMIT ?
        """, (limit,))

        items = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return items

    def get_mastered_items(self, learner_id: str, limit: int = 20) -> list[dict]:
        """
        Get mastered items ready for fluency practice.

        DEPRECATED: Use get_fluency_candidates() for skill-aware filtering.

        Args:
            learner_id: Learner identifier
            limit: Maximum items to return

        Returns:
            List of mastered items
        """
        conn = sqlite3.connect(self.mastery_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                item_id,
                node_id,
                type,
                stability,
                reps,
                difficulty,
                mastery_status
            FROM fluency_ready_items
            LIMIT ?
        """, (limit,))

        items = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return items

    def get_fluency_candidates(
        self,
        learner_id: str,
        skill: str,
        limit: int = 20
    ) -> list[dict]:
        """
        Get items for fluency practice following i-1 principle.

        Filters to mastered items at or below learner's secure level for the skill.
        This ensures fluency practice uses familiar content (Nation's framework).

        Args:
            learner_id: Learner identifier
            skill: Target skill ('reading', 'listening', 'speaking', 'writing')
            limit: Maximum items to return

        Returns:
            List of items ready for fluency practice
        """
        # Get learner's secure level for this skill (i-1 filter)
        secure_level = get_secure_level(learner_id, skill)
        secure_numeric = cefr_to_numeric(secure_level)

        # Connect to both databases
        mastery_conn = sqlite3.connect(self.mastery_db_path)
        mastery_conn.row_factory = sqlite3.Row

        # Also need KG database for CEFR levels
        kg_conn = sqlite3.connect(self.kg_db_path)
        kg_conn.row_factory = sqlite3.Row

        # Query with CEFR filtering
        # Note: We attach kg.sqlite to query nodes.cefr_level
        mastery_conn.execute(f"ATTACH DATABASE '{self.kg_db_path}' AS kg")

        cursor = mastery_conn.cursor()
        cursor.execute("""
            SELECT
                i.item_id,
                i.node_id,
                i.type,
                i.skill,
                i.stability,
                i.reps,
                i.difficulty,
                i.mastery_status,
                n.cefr_level
            FROM items i
            JOIN kg.nodes n ON i.node_id = n.node_id
            WHERE i.mastery_status IN ('mastered', 'fluency_ready')
              AND i.skill = ?
              AND i.stability >= 21.0
              AND i.reps >= 3
              AND n.cefr_level IS NOT NULL
            ORDER BY i.stability DESC, i.last_review ASC
            LIMIT ?
        """, (skill, limit))

        items = []
        for row in cursor.fetchall():
            item = dict(row)
            # Filter by CEFR level (i-1 principle)
            item_cefr_numeric = cefr_to_numeric(item["cefr_level"])
            if item_cefr_numeric <= secure_numeric:
                items.append(item)

        mastery_conn.close()
        kg_conn.close()

        return items

    def plan_session(
        self,
        learner_id: str,
        duration_minutes: int = 20,
        learner_preference: dict[str, float] | None = None
    ) -> SessionPlan:
        """
        Plan a balanced session across four strands.

        Args:
            learner_id: Learner identifier
            duration_minutes: Target session duration
            learner_preference: Optional strand preference override

        Returns:
            SessionPlan with exercises across all strands
        """
        # 1. Get current strand balance
        balance = self.get_strand_balance(learner_id)

        # 2. Calculate weights (pressure to rebalance)
        weights = self.calculate_strand_weights(balance, learner_preference)

        # 3. Get available materials
        frontier = self.get_frontier_nodes(learner_id, limit=20)
        due_items = self.get_due_items(learner_id, limit=30)
        mastered = self.get_mastered_items(learner_id, limit=20)

        # 4. Strand scarcity pressure: Filter to strands with viable candidates
        # Pre-check which strands have materials available
        strand_candidates = {
            "meaning_input": frontier,  # Could filter by strand
            "meaning_output": frontier + due_items,
            "language_focused": due_items + frontier,
            "fluency": mastered
        }

        # Check which strands have candidates
        viable_strands = {
            strand: candidates
            for strand, candidates in strand_candidates.items()
            if len(candidates) > 0
        }

        if not viable_strands:
            # No materials available - return empty plan
            return SessionPlan(
                learner_id=learner_id,
                session_date=datetime.now(),
                duration_target_minutes=duration_minutes,
                exercises=[],
                strand_balance=balance,
                balance_status=self._assess_balance_status(balance),
                notes="No materials available for any strand"
            )

        # Re-normalize weights across viable strands only
        viable_weights = {
            strand: weights[strand]
            for strand in viable_strands
        }

        # Normalize to sum=4.0 (average 1.0 per viable strand)
        weight_sum = sum(viable_weights.values())
        if weight_sum > 0:
            normalized_weights = {
                strand: (weight / weight_sum) * 4.0
                for strand, weight in viable_weights.items()
            }
        else:
            # All weights are 0 - distribute evenly
            normalized_weights = {
                strand: 4.0 / len(viable_weights)
                for strand in viable_weights
            }

        # 5. Target time per strand (weighted, viable only)
        # Clamp negative weights to 0 to skip over-represented strands
        target_time_per_strand = {
            strand: max(0, duration_minutes * (normalized_weights.get(strand, 0) / 4.0))
            for strand in weights.keys()  # Keep all strands, but non-viable get 0 time
        }

        # 6. Select exercises per strand
        exercises = []

        # Meaning-input (comprehension)
        exercises.extend(
            self._select_meaning_input(
                frontier,
                target_time=target_time_per_strand["meaning_input"]
            )
        )

        # Meaning-output (communication)
        exercises.extend(
            self._select_meaning_output(
                frontier + due_items,
                target_time=target_time_per_strand["meaning_output"]
            )
        )

        # Language-focused (explicit study)
        exercises.extend(
            self._select_language_focused(
                due_items + frontier,
                target_time=target_time_per_strand["language_focused"]
            )
        )

        # Fluency (automaticity)
        exercises.extend(
            self._select_fluency(
                mastered,
                target_time=target_time_per_strand["fluency"]
            )
        )

        # 7. Determine balance status
        balance_status = self._assess_balance_status(balance)

        # 8. Create session plan
        plan = SessionPlan(
            learner_id=learner_id,
            session_date=datetime.now(),
            duration_target_minutes=duration_minutes,
            exercises=exercises,
            strand_balance=balance,
            balance_status=balance_status,
            notes=self._generate_session_notes(balance, weights, exercises)
        )

        return plan

    def _select_meaning_input(
        self,
        candidates: list[dict],
        target_time: float
    ) -> list[Exercise]:
        """Select meaning-input exercises (comprehension)."""
        exercises = []

        # Filter to items with meaning_input strand
        input_candidates = [
            c for c in candidates
            if c.get("primary_strand") == "meaning_input"
        ]

        # Sort by priority (new items to expand comprehension, then due reviews)
        input_candidates.sort(
            key=lambda x: (
                1 if x.get("last_review") else 0,  # New items first
                -(x.get("stability", 0) or 0)        # Then by stability
            )
        )

        # Select exercises up to target time
        time_allocated = 0
        for candidate in input_candidates:
            if time_allocated >= target_time:
                break

            # Estimate 2 minutes per comprehension exercise (longer than production)
            duration = 2

            exercise = Exercise(
                strand="meaning_input",
                node_id=candidate.get("node_id", ""),
                item_id=candidate.get("item_id"),
                exercise_type="comprehension",
                duration_estimate_min=duration,
                priority_score=1.0,
                instructions=f"Understand {candidate.get('node_id', 'item')} in context",
                metadata=candidate
            )

            exercises.append(exercise)
            time_allocated += duration

        return exercises

    def _select_meaning_output(
        self,
        candidates: list[dict],
        target_time: float
    ) -> list[Exercise]:
        """Select meaning-output exercises (communication)."""
        # TODO: Implement selection logic
        exercises = []

        # Filter to items with meaning_output strand
        output_candidates = [
            c for c in candidates
            if c.get("primary_strand") == "meaning_output"
        ]

        # Prioritize due items (review) over new
        output_candidates.sort(
            key=lambda x: (
                0 if x.get("last_review") else 1,  # Due items first
                -(x.get("stability", 0) or 0)       # Then by stability
            )
        )

        # Select exercises up to target time
        time_allocated = 0
        for candidate in output_candidates:
            if time_allocated >= target_time:
                break

            # Estimate 1 minute per output exercise
            duration = 1

            exercise = Exercise(
                strand="meaning_output",
                node_id=candidate.get("node_id", ""),
                item_id=candidate.get("item_id"),
                exercise_type="production",
                duration_estimate_min=duration,
                priority_score=1.0,
                instructions=f"Communicate using {candidate.get('node_id', 'item')}",
                metadata=candidate
            )

            exercises.append(exercise)
            time_allocated += duration

        return exercises

    def _select_language_focused(
        self,
        candidates: list[dict],
        target_time: float
    ) -> list[Exercise]:
        """Select language-focused exercises (explicit study)."""
        # TODO: Implement full selection logic
        exercises = []

        # Filter to language-focused items
        lfl_candidates = [
            c for c in candidates
            if c.get("primary_strand") == "language_focused"
        ]

        # Prioritize due items
        lfl_candidates.sort(
            key=lambda x: (
                0 if x.get("last_review") else 1,
                -(x.get("stability", 0) or 0)
            )
        )

        time_allocated = 0
        for candidate in lfl_candidates:
            if time_allocated >= target_time:
                break

            duration = 1  # 1 minute per drill

            exercise = Exercise(
                strand="language_focused",
                node_id=candidate.get("node_id", ""),
                item_id=candidate.get("item_id"),
                exercise_type="controlled_drill",
                duration_estimate_min=duration,
                priority_score=1.0,
                instructions=f"Practice {candidate.get('node_id', 'item')} (focus on accuracy)",
                metadata=candidate
            )

            exercises.append(exercise)
            time_allocated += duration

        return exercises

    def _select_fluency(
        self,
        candidates: list[dict],
        target_time: float
    ) -> list[Exercise]:
        """Select fluency exercises (automaticity with mastered content)."""
        exercises = []

        # All candidates are already mastered (from fluency_ready_items view)
        # Select items not recently practiced for fluency

        time_allocated = 0
        for candidate in candidates:
            if time_allocated >= target_time:
                break

            duration = 1  # 1 minute per fluency exercise

            exercise = Exercise(
                strand="fluency",
                node_id=candidate.get("node_id", ""),
                item_id=candidate.get("item_id"),
                exercise_type="speed_drill",
                duration_estimate_min=duration,
                priority_score=1.0,
                instructions=f"Speed practice: {candidate.get('node_id', 'item')} (focus on fluency, not accuracy)",
                metadata=candidate
            )

            exercises.append(exercise)
            time_allocated += duration

        return exercises

    def _assess_balance_status(self, balance: StrandBalance) -> str:
        """Assess whether balance is acceptable."""
        strands = ["meaning_input", "meaning_output", "language_focused", "fluency"]

        max_deviation = max(
            abs(balance.deviation_from_target(s))
            for s in strands
        )

        if max_deviation <= TOLERANCE_PERCENTAGE:
            return "balanced"
        if max_deviation <= 0.10:
            return "slight_imbalance"
        return "severe_imbalance"

    def _generate_session_notes(
        self,
        balance: StrandBalance,
        weights: dict[str, float],
        exercises: list[Exercise]
    ) -> str:
        """Generate notes about session planning decisions."""
        notes = []

        # Report balance status
        notes.append("Recent strand distribution:")
        for strand in ["meaning_input", "meaning_output", "language_focused", "fluency"]:
            pct = balance.get_percentage(strand) * 100
            notes.append(f"  {strand}: {pct:.1f}%")

        # Report adjustments
        notes.append("\nThis session emphasizes:")
        emphasized = sorted(weights.items(), key=lambda x: x[1], reverse=True)
        for strand, weight in emphasized[:2]:  # Top 2
            if weight > 1.1:  # More than 10% above neutral
                notes.append(f"  {strand} (rebalancing)")

        # Report exercise breakdown
        strand_counts = {}
        for ex in exercises:
            strand_counts[ex.strand] = strand_counts.get(ex.strand, 0) + 1

        notes.append("\nExercises selected:")
        for strand, count in strand_counts.items():
            notes.append(f"  {strand}: {count} exercises")

        return "\n".join(notes)


def update_mastery_status(
    item_id: str,
    db_path: Path,
    criteria: dict | None = None
) -> tuple[str, str]:
    """
    Update mastery status for an item based on FSRS data.

    Args:
        item_id: Item to check
        db_path: Path to mastery database
        criteria: Mastery criteria (optional)

    Returns:
        Tuple of (old_status, new_status)
    """
    criteria = criteria or DEFAULT_MASTERY_CRITERIA

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get item data
    cursor.execute("""
        SELECT
            i.item_id,
            i.stability,
            i.reps,
            i.mastery_status,
            AVG(rh.quality) as avg_quality
        FROM items i
        LEFT JOIN review_history rh ON i.item_id = rh.item_id
        WHERE i.item_id = ?
        GROUP BY i.item_id
    """, (item_id,))

    item = cursor.fetchone()
    if not item:
        conn.close()
        return ("not_found", "not_found")

    old_status = item["mastery_status"]

    # Check mastery criteria
    stability = item["stability"] or 0
    reps = item["reps"] or 0
    avg_quality = item["avg_quality"] or 0

    if (stability >= criteria["stability_days"] and
        reps >= criteria["min_reps"] and
        avg_quality >= criteria["avg_quality"]):
        new_status = "mastered"
    elif reps == 0:
        new_status = "new"
    else:
        new_status = "learning"

    # Update if changed
    if old_status != new_status:
        cursor.execute("""
            UPDATE items
            SET mastery_status = ?,
                last_mastery_check = CURRENT_TIMESTAMP
            WHERE item_id = ?
        """, (new_status, item_id))
        conn.commit()

    conn.close()

    return (old_status, new_status)
