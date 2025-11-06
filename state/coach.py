"""
Atomic Coaching Tools for LLM Orchestrator

This module provides high-level, transactional operations that wrap complex
multi-table database updates into simple function calls that an LLM can reliably use.

Design Principles:
1. Single Responsibility: Each function does ONE complete thing
2. Minimal LLM Input: LLM only provides pedagogical judgments
3. Comprehensive Output: Return everything LLM needs for next decision
4. Transactional: All related tables updated atomically

Reference: STRATEGY.md "Hybrid Architecture: LLM + Atomic Tools"
"""

import json
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from state.session_planner import (
    SessionPlanner,
    StrandBalance,
    Exercise,
    update_mastery_status,
    DEFAULT_MASTERY_CRITERIA
)
from state.fsrs import ReviewCard, review_card, DEFAULT_W


@dataclass
class SessionInfo:
    """Active session metadata."""
    session_id: str
    learner_id: str
    start_time: datetime
    duration_target_minutes: int
    exercises_completed: int
    exercises_remaining: int
    exercises_planned: int  # Total exercises planned at start
    current_strand_balance: StrandBalance
    session_notes: str
    mastery_changes: int = 0  # Counter for items that changed mastery status
    total_quality: float = 0.0  # Sum of quality scores (for averaging)


@dataclass
class ExerciseResult:
    """Result of recording an exercise."""
    success: bool
    item_id: str
    quality: int
    next_review_date: str
    new_stability: float
    new_difficulty: float
    mastery_status: str
    mastery_changed: bool
    strand_balance: Dict[str, float]
    session_progress: str
    feedback_for_llm: str


class Coach:
    """
    Atomic coaching operations for LLM orchestrator.

    This class wraps session planning, FSRS scheduling, mastery tracking,
    and strand balancing into simple, transactional operations.
    """

    def __init__(
        self,
        kg_db_path: Optional[Path] = None,
        mastery_db_path: Optional[Path] = None,
        mastery_criteria: Optional[Dict] = None
    ):
        """
        Initialize coaching tools.

        Args:
            kg_db_path: Path to knowledge graph database
            mastery_db_path: Path to mastery database
            mastery_criteria: Custom mastery thresholds (optional)
        """
        self.kg_db_path = kg_db_path or Path(__file__).parent.parent / "kg.sqlite"
        self.mastery_db_path = mastery_db_path or Path(__file__).parent / "mastery.sqlite"
        self.mastery_criteria = mastery_criteria or DEFAULT_MASTERY_CRITERIA

        self.planner = SessionPlanner(
            kg_db_path=self.kg_db_path,
            mastery_db_path=self.mastery_db_path,
            mastery_criteria=self.mastery_criteria
        )

        # Active sessions (session_id -> SessionInfo)
        self.active_sessions: Dict[str, SessionInfo] = {}

    def preview_session(
        self,
        learner_id: str,
        duration_minutes: int = 20,
        learner_preference: Optional[Dict[str, float]] = None
    ) -> Dict:
        """
        Preview a session plan WITHOUT starting the session.

        This allows the LLM to show learners what's planned and negotiate
        adjustments before committing to a session. Returns the same structure
        as start_session() but without creating an active session.

        Args:
            learner_id: Learner identifier
            duration_minutes: Target session duration (default: 20)
            learner_preference: Optional strand preferences (defeasible)

        Returns:
            Dictionary with exercises, balance status, notes (no session_id)
        """
        # Generate session plan
        plan = self.planner.plan_session(
            learner_id=learner_id,
            duration_minutes=duration_minutes,
            learner_preference=learner_preference
        )

        return {
            "exercises": [
                {
                    "strand": ex.strand,
                    "node_id": ex.node_id,
                    "item_id": ex.item_id,
                    "exercise_type": ex.exercise_type,
                    "duration_estimate_min": ex.duration_estimate_min,
                    "instructions": ex.instructions
                }
                for ex in plan.exercises
            ],
            "total_exercises": len(plan.exercises),
            "balance_status": plan.balance_status,
            "current_balance": {
                "meaning_input": f"{plan.strand_balance.meaning_input * 100:.1f}%",
                "meaning_output": f"{plan.strand_balance.meaning_output * 100:.1f}%",
                "language_focused": f"{plan.strand_balance.language_focused * 100:.1f}%",
                "fluency": f"{plan.strand_balance.fluency * 100:.1f}%"
            },
            "notes": plan.notes,
            "llm_guidance": self._generate_session_guidance(plan)
        }

    def adjust_focus(
        self,
        goal_description: str,
        current_balance: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """
        Translate a learner's goal into strand preference weights.

        This is a HEURISTIC function that maps common goals to strand emphasis.
        The LLM can override these mappings with its own reasoning.

        Args:
            goal_description: Natural language goal (e.g., "practice travel Spanish")
            current_balance: Optional current strand percentages

        Returns:
            Dictionary of strand weights (higher = more emphasis)

        Examples:
            "prepare for travel" → emphasize meaning_output + relevant topics
            "improve grammar" → emphasize language_focused
            "build fluency" → emphasize fluency + meaning_output
            "understand native speakers" → emphasize meaning_input
        """
        goal_lower = goal_description.lower()

        # Default: equal weights
        weights = {
            "meaning_input": 1.0,
            "meaning_output": 1.0,
            "language_focused": 1.0,
            "fluency": 1.0
        }

        # Goal-based heuristics
        if any(word in goal_lower for word in ["travel", "trip", "vacation", "booking", "hotel", "restaurant"]):
            weights["meaning_output"] = 2.0  # Transactional functions
            weights["meaning_input"] = 1.5   # Comprehension

        elif any(word in goal_lower for word in ["grammar", "correct", "accuracy", "mistakes", "rules"]):
            weights["language_focused"] = 2.5
            weights["meaning_output"] = 0.5  # Less focus on free production

        elif any(word in goal_lower for word in ["fluent", "fluency", "speed", "automatic", "faster"]):
            weights["fluency"] = 2.5
            weights["meaning_output"] = 1.5
            weights["language_focused"] = 0.5

        elif any(word in goal_lower for word in ["understand", "listening", "comprehension", "podcast", "movie"]):
            weights["meaning_input"] = 2.5
            weights["meaning_output"] = 0.8

        elif any(word in goal_lower for word in ["speak", "speaking", "conversation", "talk", "communicate"]):
            weights["meaning_output"] = 2.5
            weights["meaning_input"] = 1.2

        elif any(word in goal_lower for word in ["write", "writing", "email", "letter", "essay"]):
            weights["meaning_output"] = 2.0
            weights["language_focused"] = 1.5

        # If current balance provided, reduce weights for over-represented strands
        if current_balance:
            for strand, percentage in current_balance.items():
                if percentage > 0.35:  # Over 35%
                    weights[strand] *= 0.5  # Reduce emphasis

        # Bound weights to [0, 2.0] range
        for strand in weights:
            weights[strand] = max(0.0, min(2.0, weights[strand]))

        # Normalize weights to sum to 4.0 (average of 1.0 per strand)
        total = sum(weights.values())
        if total > 0:
            scale_factor = 4.0 / total
            for strand in weights:
                weights[strand] *= scale_factor

        return weights

    def start_session(
        self,
        learner_id: str,
        duration_minutes: int = 20,
        learner_preference: Optional[Dict[str, float]] = None
    ) -> Dict:
        """
        Start a new coaching session.

        This is the first function LLM calls. It:
        1. Generates a session plan with balanced exercises
        2. Stores session metadata
        3. Returns exercises and balance info

        Args:
            learner_id: Learner identifier
            duration_minutes: Target session duration (default: 20)
            learner_preference: Optional strand preferences (defeasible)

        Returns:
            Dictionary with session_id, exercises, balance status, notes
        """
        # Generate session plan
        plan = self.planner.plan_session(
            learner_id=learner_id,
            duration_minutes=duration_minutes,
            learner_preference=learner_preference
        )

        # Create session record
        session_id = str(uuid4())
        session_info = SessionInfo(
            session_id=session_id,
            learner_id=learner_id,
            start_time=datetime.now(timezone.utc),
            duration_target_minutes=duration_minutes,
            exercises_completed=0,
            exercises_remaining=len(plan.exercises),
            exercises_planned=len(plan.exercises),
            current_strand_balance=plan.strand_balance,
            session_notes=plan.notes
        )

        self.active_sessions[session_id] = session_info

        # Log session start
        self._log_session_start(session_id, learner_id, duration_minutes)

        return {
            "session_id": session_id,
            "exercises": [
                {
                    "strand": ex.strand,
                    "node_id": ex.node_id,
                    "item_id": ex.item_id,
                    "exercise_type": ex.exercise_type,
                    "duration_estimate_min": ex.duration_estimate_min,
                    "instructions": ex.instructions
                }
                for ex in plan.exercises
            ],
            "total_exercises": len(plan.exercises),
            "balance_status": plan.balance_status,
            "current_balance": {
                "meaning_input": f"{plan.strand_balance.meaning_input * 100:.1f}%",
                "meaning_output": f"{plan.strand_balance.meaning_output * 100:.1f}%",
                "language_focused": f"{plan.strand_balance.language_focused * 100:.1f}%",
                "fluency": f"{plan.strand_balance.fluency * 100:.1f}%"
            },
            "notes": plan.notes,
            "llm_guidance": self._generate_session_guidance(plan)
        }

    def record_exercise(
        self,
        session_id: str,
        item_id: str,
        quality: int,
        learner_response: str,
        duration_seconds: float,
        strand: str,
        exercise_type: str = "production"
    ) -> ExerciseResult:
        """
        Record a completed exercise (ATOMIC OPERATION).

        This is the core function LLM calls after each exercise. It handles:
        1. FSRS parameter updates (stability, difficulty)
        2. Mastery status progression check
        3. Strand-specific logging
        4. Review history recording
        5. Session progress tracking

        All database writes are transactional (all-or-nothing).

        Args:
            session_id: Active session identifier
            item_id: Item being practiced
            quality: LLM's quality assessment (0-5 scale)
            learner_response: What learner said/wrote (for logging)
            duration_seconds: How long exercise took
            strand: Which strand ('meaning_input', 'meaning_output', etc.)
            exercise_type: Type of exercise (default: 'production')

        Returns:
            ExerciseResult with FSRS updates, mastery status, balance, feedback
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found. Call start_session() first.")

        session = self.active_sessions[session_id]

        conn = sqlite3.connect(self.mastery_db_path)
        conn.row_factory = sqlite3.Row

        try:
            cursor = conn.cursor()

            # 1. Get or create item
            cursor.execute("SELECT * FROM items WHERE item_id = ?", (item_id,))
            row = cursor.fetchone()

            if row:
                # Existing item - update FSRS
                current_card = ReviewCard(
                    stability=row['stability'] or 0.0,
                    difficulty=row['difficulty'] or 5.0,
                    reps=row['reps'] or 0,
                    last_review=datetime.fromisoformat(row['last_review']) if row['last_review'] else None
                )
                old_mastery_status = row['mastery_status']
            else:
                # New item - initialize
                current_card = ReviewCard(
                    stability=0.0,
                    difficulty=5.0,
                    reps=0,
                    last_review=None
                )
                old_mastery_status = 'new'

            # 2. Update FSRS parameters
            review_time = datetime.now(timezone.utc)
            updated_card, review_result = review_card(
                current_card,
                quality,
                review_time=review_time,
                w=DEFAULT_W
            )

            # 3. Update or insert item
            # Extract node_id from item_id (e.g., "card.es.ser_vs_estar.001" → "card.es.ser_vs_estar")
            node_id = '.'.join(item_id.split('.')[:-1]) if '.' in item_id else item_id

            cursor.execute("""
                INSERT INTO items (
                    item_id, node_id, type, last_review, stability, difficulty, reps,
                    primary_strand, mastery_status, last_mastery_check
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(item_id) DO UPDATE SET
                    last_review = excluded.last_review,
                    stability = excluded.stability,
                    difficulty = excluded.difficulty,
                    reps = excluded.reps,
                    primary_strand = excluded.primary_strand,
                    last_mastery_check = excluded.last_mastery_check
            """, (
                item_id,
                node_id,
                exercise_type,
                review_time.isoformat(),
                updated_card.stability,
                updated_card.difficulty,
                updated_card.reps,
                strand,
                old_mastery_status,  # Will be updated by mastery check
                review_time.isoformat()
            ))

            # 4. Log to review_history
            cursor.execute("""
                INSERT INTO review_history (
                    item_id, review_time, quality,
                    stability_before, stability_after,
                    difficulty_before, difficulty_after,
                    strand, exercise_type
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item_id,
                review_time.isoformat(),
                quality,
                current_card.stability,
                updated_card.stability,
                current_card.difficulty,
                updated_card.difficulty,
                strand,
                exercise_type
            ))

            # 5. Log to strand-specific table
            self._log_to_strand_table(
                cursor,
                strand,
                item_id,
                session_id,
                quality,
                duration_seconds,
                learner_response
            )

            # 6. Check mastery status
            old_status, new_status = self._check_mastery_status(cursor, item_id)
            mastery_changed = old_status != new_status

            # 7. Update session progress
            session.exercises_completed += 1
            session.exercises_remaining -= 1
            session.total_quality += quality
            if mastery_changed:
                session.mastery_changes += 1

            conn.commit()

            # 8. Get updated strand balance
            balance = self.planner.get_strand_balance(session.learner_id)

            # 9. Generate feedback for LLM
            feedback = self._generate_exercise_feedback(
                quality,
                updated_card,
                new_status,
                mastery_changed,
                balance
            )

            return ExerciseResult(
                success=True,
                item_id=item_id,
                quality=quality,
                next_review_date=review_result.next_review_date.isoformat(),
                new_stability=updated_card.stability,
                new_difficulty=updated_card.difficulty,
                mastery_status=new_status,
                mastery_changed=mastery_changed,
                strand_balance={
                    "meaning_input": balance.meaning_input,
                    "meaning_output": balance.meaning_output,
                    "language_focused": balance.language_focused,
                    "fluency": balance.fluency
                },
                session_progress=f"{session.exercises_completed}/{session.exercises_completed + session.exercises_remaining}",
                feedback_for_llm=feedback
            )

        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to record exercise: {e}") from e

        finally:
            conn.close()

    def end_session(self, session_id: str) -> Dict:
        """
        End an active session.

        Finalizes session statistics and logs summary.

        Args:
            session_id: Session to end

        Returns:
            Dictionary with session summary
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.active_sessions[session_id]
        end_time = datetime.now(timezone.utc)
        duration_actual = (end_time - session.start_time).total_seconds() / 60

        # Log session end
        self._log_session_end(
            session_id,
            session.learner_id,
            session.exercises_completed,
            duration_actual
        )

        # Get final strand balance
        balance = self.planner.get_strand_balance(session.learner_id)

        summary = {
            "session_id": session_id,
            "learner_id": session.learner_id,
            "exercises_completed": session.exercises_completed,
            "duration_target_min": session.duration_target_minutes,
            "duration_actual_min": round(duration_actual, 1),
            "final_balance": {
                "meaning_input": f"{balance.meaning_input * 100:.1f}%",
                "meaning_output": f"{balance.meaning_output * 100:.1f}%",
                "language_focused": f"{balance.language_focused * 100:.1f}%",
                "fluency": f"{balance.fluency * 100:.1f}%"
            },
            "balance_status": self._assess_balance_status(balance),
            "notes": session.session_notes
        }

        # Remove from active sessions
        del self.active_sessions[session_id]

        return summary

    # Helper methods

    def _log_session_start(self, session_id: str, learner_id: str, duration: int):
        """Log session start to database."""
        conn = sqlite3.connect(self.mastery_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                learner_id TEXT NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                duration_target_min INTEGER,
                duration_actual_min REAL,
                exercises_completed INTEGER DEFAULT 0
            )
        """)

        cursor.execute("""
            INSERT INTO sessions (session_id, learner_id, start_time, duration_target_min)
            VALUES (?, ?, ?, ?)
        """, (session_id, learner_id, datetime.now(timezone.utc).isoformat(), duration))

        conn.commit()
        conn.close()

    def _log_session_end(self, session_id: str, learner_id: str, exercises: int, duration: float):
        """Log session end to database (both sessions and session_log tables)."""
        if session_id not in self.active_sessions:
            # Session already removed, can't get full metrics
            return

        session = self.active_sessions[session_id]
        balance = self.planner.get_strand_balance(learner_id)
        balance_status = self._assess_balance_status(balance)

        # Calculate quality average
        quality_avg = session.total_quality / session.exercises_completed if session.exercises_completed > 0 else 0.0

        conn = sqlite3.connect(self.mastery_db_path)
        cursor = conn.cursor()

        # Update sessions table (backward compatibility)
        cursor.execute("""
            UPDATE sessions
            SET end_time = ?, exercises_completed = ?, duration_actual_min = ?
            WHERE session_id = ?
        """, (datetime.now(timezone.utc).isoformat(), exercises, duration, session_id))

        # Insert into session_log table (new structured logging)
        cursor.execute("""
            INSERT INTO session_log (
                session_id, learner_id, started_at, ended_at,
                duration_target_min, duration_actual_min,
                exercises_planned, exercises_completed,
                strand_mi_pct, strand_mo_pct, strand_lf_pct, strand_fl_pct,
                balance_status, quality_avg, mastery_changes, notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            learner_id,
            session.start_time.isoformat(),
            datetime.now(timezone.utc).isoformat(),
            session.duration_target_minutes,
            duration,
            session.exercises_planned,
            exercises,
            balance.meaning_input * 100,
            balance.meaning_output * 100,
            balance.language_focused * 100,
            balance.fluency * 100,
            balance_status,
            quality_avg,
            session.mastery_changes,
            session.session_notes
        ))

        conn.commit()
        conn.close()

    def _log_to_strand_table(
        self,
        cursor,
        strand: str,
        item_id: str,
        session_id: str,
        quality: int,
        duration_seconds: float,
        response_text: str
    ):
        """Log exercise to appropriate strand table."""
        session_date = datetime.now(timezone.utc).date().isoformat()
        node_id = '.'.join(item_id.split('.')[:-1]) if '.' in item_id else item_id

        if strand == 'meaning_input':
            # Schema: node_id, item_id, session_date, comprehension_quality,
            # understood_key_points, required_repetitions, task_type, notes
            cursor.execute("""
                INSERT INTO meaning_input_log (
                    node_id, item_id, session_date, comprehension_quality,
                    understood_key_points, required_repetitions, task_type, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                node_id,
                item_id,
                session_date,
                quality,
                True if quality >= 3 else False,  # Success if quality >= 3
                1,  # Could track this later
                'comprehension',
                response_text[:200]
            ))

        elif strand == 'meaning_output':
            # Schema: node_id, item_id, session_date, communication_successful,
            # quality, errors_noted, required_clarification, task_type, notes
            cursor.execute("""
                INSERT INTO meaning_output_log (
                    node_id, item_id, session_date, communication_successful,
                    quality, errors_noted, required_clarification, task_type, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                node_id,
                item_id,
                session_date,
                True if quality >= 3 else False,
                quality,
                "",  # Could extract errors later
                False,  # Could track this later
                'production',
                response_text
            ))

        elif strand == 'fluency':
            # Schema: item_id, session_date, duration_seconds, output_word_count,
            # words_per_minute, pause_count, hesitation_markers, baseline_wpm,
            # improvement_pct, smoothness, improvement_feel, notes
            words = len(response_text.split())
            wpm = (words / duration_seconds) * 60 if duration_seconds > 0 else 0

            cursor.execute("""
                INSERT INTO fluency_metrics (
                    item_id, session_date, duration_seconds, output_word_count,
                    words_per_minute, pause_count, hesitation_markers,
                    baseline_wpm, improvement_pct, smoothness, improvement_feel, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item_id,
                session_date,
                duration_seconds,
                words,
                wpm,
                0,  # Could track pauses later
                0,  # Could track hesitations later
                None,  # Could track baseline later
                None,  # Could calculate improvement later
                'smooth' if quality >= 4 else 'hesitant',
                'improving' if quality >= 3 else 'stable',
                response_text[:100]
            ))

        # language_focused doesn't have a separate log table (uses review_history)

    def _check_mastery_status(self, cursor, item_id: str) -> Tuple[str, str]:
        """Check and update mastery status."""
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
            return ('not_found', 'not_found')

        old_status = item['mastery_status'] or 'new'
        stability = item['stability'] or 0
        reps = item['reps'] or 0
        avg_quality = item['avg_quality'] or 0

        # Check mastery criteria
        if (stability >= self.mastery_criteria['stability_days'] and
            reps >= self.mastery_criteria['min_reps'] and
            avg_quality >= self.mastery_criteria['avg_quality']):
            new_status = 'mastered'
        elif reps == 0:
            new_status = 'new'
        else:
            new_status = 'learning'

        # Update if changed
        if old_status != new_status:
            cursor.execute("""
                UPDATE items
                SET mastery_status = ?, last_mastery_check = ?
                WHERE item_id = ?
            """, (new_status, datetime.now(timezone.utc).isoformat(), item_id))

        return (old_status, new_status)

    def _generate_session_guidance(self, plan) -> str:
        """Generate guidance for LLM at session start."""
        if plan.balance_status == 'balanced':
            return "Strand balance is good. Proceed with planned exercises."
        elif plan.balance_status == 'slight_imbalance':
            return f"Strand balance slightly off. This session emphasizes under-represented strands."
        else:
            return f"Strand balance needs correction. Focus on exercises that restore balance."

    def _generate_exercise_feedback(
        self,
        quality: int,
        card: ReviewCard,
        mastery_status: str,
        mastery_changed: bool,
        balance: StrandBalance
    ) -> str:
        """Generate feedback for LLM after exercise."""
        feedback_parts = []

        # Quality acknowledgment
        if quality >= 4:
            feedback_parts.append("Strong performance!")
        elif quality >= 3:
            feedback_parts.append("Good effort.")
        else:
            feedback_parts.append("Keep practicing.")

        # FSRS info
        feedback_parts.append(f"Stability: {card.stability:.1f} days")

        # Mastery progression
        if mastery_changed:
            feedback_parts.append(f"Status changed to: {mastery_status}")
        else:
            feedback_parts.append(f"Status: {mastery_status}")

        # Balance reminder if needed
        deviations = [
            abs(balance.meaning_input - 0.25),
            abs(balance.meaning_output - 0.25),
            abs(balance.language_focused - 0.25),
            abs(balance.fluency - 0.25)
        ]
        if max(deviations) > 0.10:
            feedback_parts.append("⚠ Strand balance needs attention")

        return " | ".join(feedback_parts)

    def _assess_balance_status(self, balance: StrandBalance) -> str:
        """Assess balance status."""
        strands = ['meaning_input', 'meaning_output', 'language_focused', 'fluency']
        max_deviation = max(
            abs(balance.deviation_from_target(s))
            for s in strands
        )

        if max_deviation <= 0.05:
            return 'balanced'
        elif max_deviation <= 0.10:
            return 'slight_imbalance'
        else:
            return 'severe_imbalance'
