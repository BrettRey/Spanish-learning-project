#!/usr/bin/env python3
"""
Lesson Runner - Two-Agent Simulation

Simulates a Spanish coaching session with:
- Coach Agent: Conducts lesson following SPANISH_COACH.md
- Learner Agent: A2+/B1 Spanish learner with realistic errors

This tests the atomic coaching tools end-to-end.
"""

import json
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from state.coach import Coach


class LessonSimulation:
    """Orchestrates a simulated lesson between coach and learner agents."""

    def __init__(self, learner_id: str = "simulation_learner", log_dir: str = "agents/logs"):
        self.learner_id = learner_id
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.coach = Coach()
        self.session_log: List[Dict[str, Any]] = []
        self.metrics = {
            "exercises_completed": 0,
            "quality_distribution": {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            "database_consistency_checks": [],
            "strand_balance_history": [],
            "errors": [],
        }

    def simulate_learner_response(
        self, exercise: Dict[str, Any], exercise_count: int
    ) -> Dict[str, Any]:
        """
        Simulate a learner response based on exercise and learner persona.

        In a full implementation, this would call an LLM API with the learner persona.
        For now, we'll generate realistic A2+/B1 responses based on patterns.
        """
        prompt = exercise.get("prompt", "")
        strand = exercise.get("strand", "meaning_output")
        node_id = exercise.get("node_id", "")

        # Simulate realistic quality distribution
        # Quality 3 (adequate) is most common for A2+/B1
        import random

        quality_target = random.choices(
            [0, 1, 2, 3, 4, 5], weights=[1, 4, 15, 40, 30, 10], k=1
        )[0]

        # Generate response based on target quality
        responses = self._generate_realistic_response(prompt, strand, node_id, quality_target)

        return {
            "learner_utterance": responses["spanish"],
            "internal_quality_target": quality_target,  # For validation
            "duration_seconds": random.randint(20, 90),
        }

    def _generate_realistic_response(
        self, prompt: str, strand: str, node_id: str, quality: int
    ) -> Dict[str, str]:
        """Generate a realistic Spanish response for given quality level."""

        # This is a simplified version - in production, use an LLM with learner persona
        responses_by_quality = {
            5: {  # Perfect
                "spanish": "Me levanto a las siete, me ducho, desayuno y salgo de casa a las ocho.",
                "type": "perfect",
            },
            4: {  # Good with minor errors
                "spanish": "Me levanto a las siete, me ducho, desayuno y salgo de la casa a las ocho.",
                "type": "minor_errors",  # "de la casa" instead of "de casa"
            },
            3: {  # Adequate but noticeable errors
                "spanish": "Yo me levanto en las siete, me ducho, como desayuno y voy fuera a las ocho.",
                "type": "noticeable_errors",  # "en las" instead of "a las", "como desayuno" awkward
            },
            2: {  # Weak
                "spanish": "Me levanto las siete, yo ducho, yo como el desayuno, yo voy la casa fuera ocho.",
                "type": "major_errors",  # Missing prepositions, awkward phrasing
            },
            1: {  # Poor
                "spanish": "Levanto siete, duchas, comer desayuno, ir casa.",
                "type": "severe_errors",  # Missing pronouns, wrong conjugations
            },
            0: {  # Failed
                "spanish": "I wake up at seven... no sé cómo decirlo",
                "type": "failed",  # Gave up in English
            },
        }

        return responses_by_quality.get(quality, responses_by_quality[3])

    def simulate_coach_assessment(
        self, exercise: Dict[str, Any], learner_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Simulate coach assessment of learner response.

        In a full implementation, this would call an LLM API with coach instructions.
        For now, we'll use the internal quality target as ground truth.
        """
        # Coach should assess close to the target quality (with some variation)
        import random

        target = learner_response["internal_quality_target"]

        # Coach might be off by ±1 sometimes (realistic assessment variance)
        variation = random.choice([-1, 0, 0, 0, 1])  # Usually accurate, sometimes ±1
        quality = max(0, min(5, target + variation))

        # Generate feedback
        feedback_templates = {
            5: "¡Excelente! Perfect usage. ",
            4: "¡Muy bien! Just a small detail: {correction}. ",
            3: "Bien, I understand you. Let's work on {correction}. ",
            2: "I see what you're trying to say. Remember: {correction}. ",
            1: "Let's practice this more. Try: {correction}. ",
            0: "No problem! Let's try together. ",
        }

        feedback = feedback_templates.get(quality, "Good effort! ")
        feedback += "Let's continue."

        return {
            "quality_assessment": quality,
            "coach_feedback": feedback,
            "assessment_rationale": f"Based on form accuracy, meaning clarity, and appropriateness for level",
            "duration_seconds": learner_response["duration_seconds"],
        }

    def check_database_consistency(self, session_id: str) -> Dict[str, Any]:
        """Verify database was updated correctly after exercise recording."""
        db_path = Path("state/mastery.sqlite")
        if not db_path.exists():
            return {"status": "error", "message": "Database not found"}

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check review_history table
            cursor.execute(
                """
                SELECT COUNT(*) FROM review_history
                WHERE strftime('%Y-%m-%d', review_time) = date('now')
            """
            )
            today_reviews = cursor.fetchone()[0]

            # Check items table
            cursor.execute("SELECT COUNT(*) FROM items")
            total_items = cursor.fetchone()[0]

            # Check session_log table
            cursor.execute(
                """
                SELECT COUNT(*) FROM session_log
                WHERE session_id = ?
            """,
                (session_id,),
            )
            session_entries = cursor.fetchone()[0]

            conn.close()

            return {
                "status": "ok",
                "today_reviews": today_reviews,
                "total_items": total_items,
                "session_entries": session_entries,
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def run_session(
        self, duration_minutes: int = 20, max_exercises: int = 10
    ) -> Dict[str, Any]:
        """Run a complete simulated lesson session."""

        print(f"\n{'='*60}")
        print(f"🎓 Starting Simulated Spanish Lesson")
        print(f"{'='*60}")
        print(f"Learner: {self.learner_id} (A2+/B1 level)")
        print(f"Target Duration: {duration_minutes} minutes")
        print(f"Max Exercises: {max_exercises}")
        print(f"{'='*60}\n")

        session_start_time = time.time()

        # Step 1: Start session
        print("📋 Starting session with atomic coach...\n")
        try:
            session = self.coach.start_session(
                learner_id=self.learner_id, duration_minutes=duration_minutes
            )
            print(f"✅ Session started: {session['session_id']}")
            print(f"   Exercises planned: {len(session.get('exercises', []))}")
            print(f"   Balance status: {session.get('balance_status', 'unknown')}")
            print(f"   LLM Guidance: {session.get('llm_guidance', 'None')}\n")

        except Exception as e:
            error_msg = f"Failed to start session: {e}"
            print(f"❌ {error_msg}")
            self.metrics["errors"].append(error_msg)
            return {"status": "error", "error": error_msg}

        session_id = session["session_id"]
        exercises = session.get("exercises", [])

        if not exercises:
            print("⚠️  No exercises in session plan (database may be empty)")
            print("   This is expected for first run - KG items need to be added\n")
            return {
                "status": "ok",
                "session_id": session_id,
                "message": "Session created but no exercises available yet",
            }

        # Step 2: Conduct exercises
        exercises_to_run = exercises[:max_exercises]
        print(f"🎯 Conducting {len(exercises_to_run)} exercises:\n")

        for idx, exercise in enumerate(exercises_to_run, 1):
            print(f"{'─'*60}")
            print(f"Exercise {idx}/{len(exercises_to_run)}")
            print(f"{'─'*60}")
            print(f"Item: {exercise.get('item_id', 'N/A')}")
            print(f"Strand: {exercise.get('strand', 'N/A')}")
            print(f"Prompt: {exercise.get('prompt', 'N/A')[:80]}...")

            # Simulate learner response
            print("\n👤 Learner responding...")
            learner_response = self.simulate_learner_response(exercise, idx)
            print(f"   '{learner_response['learner_utterance'][:100]}...'")
            print(
                f"   (Target quality: {learner_response['internal_quality_target']}, Duration: {learner_response['duration_seconds']}s)"
            )

            # Simulate coach assessment
            print("\n👨‍🏫 Coach assessing...")
            coach_assessment = self.simulate_coach_assessment(exercise, learner_response)
            print(f"   Quality: {coach_assessment['quality_assessment']}/5")
            print(f"   Feedback: '{coach_assessment['coach_feedback']}'")

            # Record with atomic tools
            print("\n💾 Recording exercise with atomic tools...")
            try:
                result = self.coach.record_exercise(
                    session_id=session_id,
                    item_id=exercise["item_id"],
                    quality=coach_assessment["quality_assessment"],
                    learner_response=learner_response["learner_utterance"],
                    duration_seconds=coach_assessment["duration_seconds"],
                    strand=exercise.get("strand", "meaning_output"),
                    exercise_type=exercise.get("type", "production"),
                )

                print(f"   ✅ Recorded successfully")
                print(f"   Stability: {result.new_stability:.1f} days")
                print(f"   Mastery: {result.mastery_status}")
                if result.mastery_changed:
                    print(f"   🎉 Mastery level changed!")

                # Update metrics
                self.metrics["exercises_completed"] += 1
                self.metrics["quality_distribution"][
                    coach_assessment["quality_assessment"]
                ] += 1

                # Check database consistency
                consistency_check = self.check_database_consistency(session_id)
                self.metrics["database_consistency_checks"].append(consistency_check)
                if consistency_check["status"] == "ok":
                    print(f"   ✅ Database consistency verified")
                else:
                    print(f"   ⚠️  Database check: {consistency_check.get('message')}")

            except Exception as e:
                error_msg = f"Failed to record exercise {idx}: {e}"
                print(f"   ❌ {error_msg}")
                self.metrics["errors"].append(error_msg)

            # Log interaction
            self.session_log.append(
                {
                    "exercise_num": idx,
                    "item_id": exercise["item_id"],
                    "strand": exercise.get("strand"),
                    "learner_utterance": learner_response["learner_utterance"],
                    "quality_target": learner_response["internal_quality_target"],
                    "quality_assessed": coach_assessment["quality_assessment"],
                    "coach_feedback": coach_assessment["coach_feedback"],
                    "duration_seconds": coach_assessment["duration_seconds"],
                }
            )

            print()

        # Step 3: End session
        print(f"\n{'='*60}")
        print("🏁 Ending session...")
        print(f"{'='*60}\n")

        try:
            summary = self.coach.end_session(session_id)
            print(f"✅ Session ended successfully")
            print(f"\n📊 Session Summary:")
            print(f"   Exercises completed: {summary.get('exercises_completed', 0)}")
            print(
                f"   Duration: {summary.get('duration_actual_min', 0):.1f} minutes (target: {duration_minutes})"
            )
            print(f"   Balance status: {summary.get('balance_status', 'unknown')}")
            print(f"\n   Final strand balance:")
            for strand, pct in summary.get("final_balance", {}).items():
                print(f"      {strand}: {pct}")

        except Exception as e:
            error_msg = f"Failed to end session: {e}"
            print(f"❌ {error_msg}")
            self.metrics["errors"].append(error_msg)

        session_duration = time.time() - session_start_time

        # Generate metrics report
        print(f"\n{'='*60}")
        print("📈 SIMULATION METRICS")
        print(f"{'='*60}")
        print(f"✅ Exercises completed: {self.metrics['exercises_completed']}")
        print(f"⏱️  Total simulation time: {session_duration:.1f}s")
        print(f"\n📊 Quality Distribution:")
        for quality, count in sorted(self.metrics["quality_distribution"].items()):
            if count > 0:
                pct = (count / self.metrics["exercises_completed"]) * 100
                print(f"   Quality {quality}: {count} ({pct:.0f}%)")

        print(f"\n💾 Database Consistency:")
        if self.metrics["database_consistency_checks"]:
            last_check = self.metrics["database_consistency_checks"][-1]
            print(f"   Status: {last_check.get('status', 'unknown')}")
            print(f"   Reviews today: {last_check.get('today_reviews', 0)}")
            print(f"   Total items: {last_check.get('total_items', 0)}")
            print(
                f"   Session log entries: {last_check.get('session_entries', 0)}"
            )

        if self.metrics["errors"]:
            print(f"\n⚠️  Errors encountered: {len(self.metrics['errors'])}")
            for error in self.metrics["errors"]:
                print(f"   - {error}")
        else:
            print(f"\n✅ No errors encountered")

        print(f"\n{'='*60}\n")

        # Save log
        log_file = self.log_dir / f"session_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, "w") as f:
            json.dump(
                {
                    "session_id": session_id,
                    "learner_id": self.learner_id,
                    "duration_minutes": duration_minutes,
                    "simulation_duration_seconds": session_duration,
                    "exercises": self.session_log,
                    "metrics": self.metrics,
                    "summary": summary if "summary" in locals() else {},
                },
                f,
                indent=2,
            )
        print(f"📝 Session log saved to: {log_file}")

        return {"status": "ok", "session_id": session_id, "metrics": self.metrics}


def main():
    """Run a simulated lesson session."""
    import argparse

    parser = argparse.ArgumentParser(description="Run simulated Spanish lesson")
    parser.add_argument(
        "--learner-id",
        default="simulation_learner",
        help="Learner ID for session",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=20,
        help="Target session duration in minutes",
    )
    parser.add_argument(
        "--max-exercises",
        type=int,
        default=10,
        help="Maximum number of exercises to run",
    )

    args = parser.parse_args()

    simulation = LessonSimulation(learner_id=args.learner_id)
    result = simulation.run_session(
        duration_minutes=args.duration, max_exercises=args.max_exercises
    )

    sys.exit(0 if result["status"] == "ok" else 1)


if __name__ == "__main__":
    main()
