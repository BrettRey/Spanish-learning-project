#!/usr/bin/env python3
"""
Scale Testing Framework for Lesson Simulation

Runs multiple simulated sessions to gather statistical data on:
- FSRS convergence (stability, difficulty, mastery progression)
- Strand balance evolution
- Quality distribution patterns
- Database consistency over time
- Edge case identification

Usage:
    python agents/scale_test.py --sessions 100 --learner-id scale_test_learner
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.lesson_runner import LessonSimulation


class ScaleTest:
    """Run multiple lesson simulations and collect aggregate statistics."""

    def __init__(
        self,
        learner_id: str = "scale_test_learner",
        log_dir: str = "agents/logs/scale_test",
    ):
        self.learner_id = learner_id
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.aggregate_stats = {
            "total_sessions": 0,
            "total_exercises": 0,
            "total_duration_seconds": 0,
            "quality_distribution_overall": {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            "strand_balance_evolution": [],
            "fsrs_snapshots": [],
            "errors": [],
        }

    def run_multiple_sessions(
        self,
        num_sessions: int,
        duration_minutes: int = 15,
        max_exercises: int = 8,
        delay_between_sessions: float = 0.5,
    ) -> Dict:
        """
        Run multiple sessions sequentially for the same learner.

        Args:
            num_sessions: Number of sessions to run
            duration_minutes: Target duration per session
            max_exercises: Max exercises per session
            delay_between_sessions: Seconds to wait between sessions

        Returns:
            Aggregate statistics dictionary
        """

        print(f"\n{'='*70}")
        print(f"🧪 SCALE TEST: {num_sessions} SESSIONS")
        print(f"{'='*70}")
        print(f"Learner: {self.learner_id}")
        print(f"Duration per session: {duration_minutes} minutes")
        print(f"Max exercises per session: {max_exercises}")
        print(f"{'='*70}\n")

        start_time = time.time()

        for session_num in range(1, num_sessions + 1):
            print(f"\n{'─'*70}")
            print(f"📍 SESSION {session_num}/{num_sessions}")
            print(f"{'─'*70}\n")

            # Run session
            simulation = LessonSimulation(learner_id=self.learner_id)
            result = simulation.run_session(
                duration_minutes=duration_minutes, max_exercises=max_exercises
            )

            if result["status"] != "ok":
                error_msg = f"Session {session_num} failed: {result.get('error', 'unknown')}"
                print(f"\n❌ {error_msg}\n")
                self.aggregate_stats["errors"].append(
                    {"session": session_num, "error": error_msg}
                )
                continue

            # Collect statistics
            self._collect_session_stats(session_num, simulation, result)

            # Brief pause between sessions
            if session_num < num_sessions:
                time.sleep(delay_between_sessions)

        total_duration = time.time() - start_time

        # Final analysis
        print(f"\n{'='*70}")
        print(f"✅ SCALE TEST COMPLETE")
        print(f"{'='*70}")
        print(f"Total sessions: {self.aggregate_stats['total_sessions']}")
        print(f"Total exercises: {self.aggregate_stats['total_exercises']}")
        print(f"Total test duration: {total_duration:.1f}s")
        print(f"Average session duration: {total_duration/num_sessions:.2f}s")
        print(f"{'='*70}\n")

        # Save aggregate results
        results_file = self.log_dir / f"scale_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, "w") as f:
            json.dump(
                {
                    "test_config": {
                        "num_sessions": num_sessions,
                        "duration_minutes": duration_minutes,
                        "max_exercises": max_exercises,
                        "learner_id": self.learner_id,
                    },
                    "aggregate_stats": self.aggregate_stats,
                    "test_duration_seconds": total_duration,
                },
                f,
                indent=2,
            )

        print(f"📊 Results saved to: {results_file}\n")

        return self.aggregate_stats

    def _collect_session_stats(
        self, session_num: int, simulation: LessonSimulation, result: Dict
    ):
        """Collect statistics from a completed session."""

        metrics = result.get("metrics", {})

        # Update totals
        self.aggregate_stats["total_sessions"] += 1
        self.aggregate_stats["total_exercises"] += metrics.get("exercises_completed", 0)

        # Aggregate quality distribution
        session_quality = metrics.get("quality_distribution", {})
        for quality, count in session_quality.items():
            quality_int = int(quality)
            self.aggregate_stats["quality_distribution_overall"][quality_int] += count

        # Store strand balance snapshot
        if simulation.session_log:
            # Get final balance from session summary
            try:
                from state.session_planner import SessionPlanner

                planner = SessionPlanner(
                    kg_db_path=Path("kg.sqlite"),
                    mastery_db_path=Path("state/mastery.sqlite"),
                )
                balance = planner.get_strand_balance(self.learner_id)

                self.aggregate_stats["strand_balance_evolution"].append(
                    {
                        "session": session_num,
                        "meaning_input": balance.meaning_input,
                        "meaning_output": balance.meaning_output,
                        "language_focused": balance.language_focused,
                        "fluency": balance.fluency,
                        "total_exercises": balance.total_exercises,
                    }
                )
            except Exception as e:
                pass

        # Store FSRS snapshot (sample items)
        try:
            import sqlite3

            conn = sqlite3.connect("state/mastery.sqlite")
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    item_id,
                    stability,
                    difficulty,
                    reps,
                    mastery_status
                FROM items
                ORDER BY reps DESC
                LIMIT 10
            """
            )

            items = []
            for row in cursor.fetchall():
                items.append(
                    {
                        "item_id": row[0],
                        "stability": row[1],
                        "difficulty": row[2],
                        "reps": row[3],
                        "mastery_status": row[4],
                    }
                )

            self.aggregate_stats["fsrs_snapshots"].append(
                {"session": session_num, "top_items": items}
            )

            conn.close()
        except Exception as e:
            pass

    def print_summary(self):
        """Print summary statistics."""

        print(f"\n{'='*70}")
        print(f"📊 AGGREGATE STATISTICS")
        print(f"{'='*70}\n")

        # Overall quality distribution
        print("Quality Distribution (All Sessions):")
        total_exercises = self.aggregate_stats["total_exercises"]
        if total_exercises > 0:
            for quality in range(6):
                count = self.aggregate_stats["quality_distribution_overall"][quality]
                pct = (count / total_exercises) * 100
                bar = "█" * int(pct / 2)
                print(f"  Q{quality}: {count:4d} ({pct:5.1f}%) {bar}")

        # Strand balance evolution
        print(f"\nStrand Balance Evolution:")
        if self.aggregate_stats["strand_balance_evolution"]:
            snapshots = self.aggregate_stats["strand_balance_evolution"]

            # Show first, middle, last
            indices = [0, len(snapshots) // 2, -1]
            for idx in indices:
                snapshot = snapshots[idx]
                session_num = snapshot["session"]
                print(f"\n  Session {session_num}:")
                print(
                    f"    Meaning Input:    {snapshot['meaning_input']:.1%} (target: 25%)"
                )
                print(
                    f"    Meaning Output:   {snapshot['meaning_output']:.1%} (target: 25%)"
                )
                print(
                    f"    Language Focused: {snapshot['language_focused']:.1%} (target: 25%)"
                )
                print(f"    Fluency:          {snapshot['fluency']:.1%} (target: 25%)")
                print(f"    Total Exercises:  {snapshot['total_exercises']}")

        # FSRS convergence
        print(f"\nFSRS Convergence (Top 10 Most Practiced Items):")
        if self.aggregate_stats["fsrs_snapshots"]:
            # Show progression of a few items
            first_snapshot = self.aggregate_stats["fsrs_snapshots"][0]
            last_snapshot = self.aggregate_stats["fsrs_snapshots"][-1]

            print(f"\n  Session 1:")
            for item in first_snapshot["top_items"][:5]:
                print(
                    f"    {item['item_id'][:40]:40s} | Reps: {item['reps']:2d} | "
                    f"Stability: {item['stability']:6.2f} | Difficulty: {item['difficulty']:5.2f} | "
                    f"Status: {item['mastery_status']}"
                )

            print(f"\n  Session {self.aggregate_stats['total_sessions']}:")
            for item in last_snapshot["top_items"][:5]:
                print(
                    f"    {item['item_id'][:40]:40s} | Reps: {item['reps']:2d} | "
                    f"Stability: {item['stability']:6.2f} | Difficulty: {item['difficulty']:5.2f} | "
                    f"Status: {item['mastery_status']}"
                )

        # Errors
        if self.aggregate_stats["errors"]:
            print(f"\n⚠️  Errors Encountered: {len(self.aggregate_stats['errors'])}")
            for error in self.aggregate_stats["errors"][:10]:
                print(f"  - Session {error['session']}: {error['error']}")
        else:
            print(f"\n✅ No errors encountered")

        print(f"\n{'='*70}\n")


def main():
    """Run scale test from command line."""
    import argparse

    parser = argparse.ArgumentParser(description="Run scale test with multiple sessions")
    parser.add_argument(
        "--sessions",
        type=int,
        default=100,
        help="Number of sessions to run",
    )
    parser.add_argument(
        "--learner-id",
        default="scale_test_learner",
        help="Learner ID for test",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=15,
        help="Target duration per session (minutes)",
    )
    parser.add_argument(
        "--max-exercises",
        type=int,
        default=8,
        help="Maximum exercises per session",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Delay between sessions (seconds)",
    )

    args = parser.parse_args()

    scale_test = ScaleTest(learner_id=args.learner_id)
    scale_test.run_multiple_sessions(
        num_sessions=args.sessions,
        duration_minutes=args.duration,
        max_exercises=args.max_exercises,
        delay_between_sessions=args.delay,
    )

    scale_test.print_summary()


if __name__ == "__main__":
    main()
