#!/usr/bin/env python3
"""
Analysis Tool for Scale Test Results

Analyzes session logs from scale testing to identify:
- FSRS convergence patterns
- Strand balance evolution
- Quality distribution trends
- Mastery progression rates
- System reliability metrics
- Edge cases and anomalies

Usage:
    python agents/analyze_results.py agents/logs/scale_test/scale_test_*.json
"""

import json
import sys
from pathlib import Path
from typing import Dict, List
import statistics


class ResultsAnalyzer:
    """Analyze scale test results and generate reports."""

    def __init__(self, results_file: Path):
        self.results_file = results_file
        with open(results_file) as f:
            self.data = json.load(f)

        self.config = self.data.get("test_config", {})
        self.stats = self.data.get("aggregate_stats", {})

    def analyze_all(self):
        """Run all analyses and print comprehensive report."""

        print(f"\n{'='*80}")
        print(f"📊 SCALE TEST ANALYSIS")
        print(f"{'='*80}")
        print(f"Results file: {self.results_file.name}")
        print(f"Test date: {self.results_file.stem.split('_')[-2:]}")
        print(f"{'='*80}\n")

        self.print_test_config()
        self.analyze_quality_distribution()
        self.analyze_strand_balance()
        self.analyze_fsrs_convergence()
        self.analyze_mastery_progression()
        self.analyze_reliability()
        self.identify_edge_cases()
        self.print_conclusions()

    def print_test_config(self):
        """Print test configuration."""
        print("## Test Configuration\n")
        print(f"  Sessions run: {self.config.get('num_sessions', 'N/A')}")
        print(f"  Duration per session: {self.config.get('duration_minutes', 'N/A')} minutes")
        print(f"  Max exercises per session: {self.config.get('max_exercises', 'N/A')}")
        print(f"  Learner ID: {self.config.get('learner_id', 'N/A')}")
        print(
            f"  Test duration: {self.data.get('test_duration_seconds', 0):.1f}s\n"
        )

    def analyze_quality_distribution(self):
        """Analyze quality score distribution."""
        print("## Quality Distribution\n")

        quality_dist = self.stats.get("quality_distribution_overall", {})
        total = sum(quality_dist.values())

        if total == 0:
            print("  No exercises recorded\n")
            return

        print(f"  Total exercises: {total}\n")

        # Calculate statistics
        qualities = []
        for q, count in quality_dist.items():
            qualities.extend([int(q)] * count)

        mean_quality = statistics.mean(qualities)
        median_quality = statistics.median(qualities)
        mode_quality = statistics.mode(qualities)
        stdev_quality = statistics.stdev(qualities) if len(qualities) > 1 else 0

        print(f"  Mean quality:   {mean_quality:.2f}")
        print(f"  Median quality: {median_quality:.1f}")
        print(f"  Mode quality:   {mode_quality}")
        print(f"  Std deviation:  {stdev_quality:.2f}\n")

        print("  Distribution:")
        for q in range(6):
            count = quality_dist.get(str(q), 0)
            pct = (count / total) * 100
            bar = "█" * int(pct / 2)
            print(f"    Q{q}: {count:5d} ({pct:5.1f}%) {bar}")

        # Expected for A2+/B1: Q3 (40%), Q4 (30%), Q2 (15%), Q5 (10%), Q1 (4%), Q0 (1%)
        expected = {0: 1, 1: 4, 2: 15, 3: 40, 4: 30, 5: 10}
        print("\n  Comparison to Expected A2+/B1 Distribution:")
        for q in range(6):
            actual_pct = (quality_dist.get(str(q), 0) / total) * 100
            expected_pct = expected[q]
            diff = actual_pct - expected_pct
            symbol = "✓" if abs(diff) < 5 else "⚠"
            print(
                f"    Q{q}: {actual_pct:5.1f}% (expected {expected_pct:5.1f}%, diff {diff:+5.1f}%) {symbol}"
            )

        print()

    def analyze_strand_balance(self):
        """Analyze strand balance evolution over sessions."""
        print("## Strand Balance Evolution\n")

        evolution = self.stats.get("strand_balance_evolution", [])
        if not evolution:
            print("  No strand balance data\n")
            return

        # Calculate convergence metrics
        target = 0.25

        print("  Target: 25% per strand (±5% tolerance = 20-30%)\n")

        # Show progression
        milestones = [1, 10, 25, 50, 75, 100]
        milestones = [m for m in milestones if m <= len(evolution)]

        for milestone in milestones:
            snapshot = evolution[milestone - 1]
            print(f"  Session {milestone}:")

            for strand in ["meaning_input", "meaning_output", "language_focused", "fluency"]:
                value = snapshot.get(strand, 0)
                deviation = abs(value - target)
                in_tolerance = deviation <= 0.05

                status = "✓" if in_tolerance else "⚠"
                print(
                    f"    {strand:20s}: {value:6.1%} (dev: {deviation:+5.1%}) {status}"
                )
            print()

        # Calculate convergence rate
        if len(evolution) >= 10:
            early_deviations = []
            late_deviations = []

            for snapshot in evolution[:10]:
                for strand in ["meaning_input", "meaning_output", "language_focused", "fluency"]:
                    early_deviations.append(abs(snapshot.get(strand, 0) - target))

            for snapshot in evolution[-10:]:
                for strand in ["meaning_input", "meaning_output", "language_focused", "fluency"]:
                    late_deviations.append(abs(snapshot.get(strand, 0) - target))

            early_avg = statistics.mean(early_deviations)
            late_avg = statistics.mean(late_deviations)
            improvement = ((early_avg - late_avg) / early_avg) * 100 if early_avg > 0 else 0

            print(f"  Convergence Analysis:")
            print(f"    Average deviation (sessions 1-10):  {early_avg:.1%}")
            print(f"    Average deviation (last 10):        {late_avg:.1%}")
            print(f"    Improvement:                         {improvement:+.1f}%")

            if late_avg <= 0.05:
                print(f"    Status: ✅ Converged within tolerance")
            elif improvement > 0:
                print(f"    Status: 📈 Converging (positive trend)")
            else:
                print(f"    Status: ⚠️  Not converging")

        print()

    def analyze_fsrs_convergence(self):
        """Analyze FSRS parameter convergence."""
        print("## FSRS Convergence\n")

        snapshots = self.stats.get("fsrs_snapshots", [])
        if not snapshots:
            print("  No FSRS data\n")
            return

        first = snapshots[0]
        last = snapshots[-1]

        print(f"  Comparing Session 1 vs Session {len(snapshots)}:\n")

        # Track specific items
        first_items = {item["item_id"]: item for item in first.get("top_items", [])}
        last_items = {item["item_id"]: item for item in last.get("top_items", [])}

        # Find items that appear in both
        common_items = set(first_items.keys()) & set(last_items.keys())

        if common_items:
            print(f"  Items practiced throughout ({len(common_items)} items):\n")

            for item_id in sorted(common_items)[:5]:
                first_item = first_items[item_id]
                last_item = last_items[item_id]

                stability_change = last_item["stability"] - first_item["stability"]
                difficulty_change = last_item["difficulty"] - first_item["difficulty"]
                reps_change = last_item["reps"] - first_item["reps"]

                print(f"    {item_id[:50]}")
                print(
                    f"      Stability:  {first_item['stability']:6.2f} → {last_item['stability']:6.2f} "
                    f"({stability_change:+6.2f} days)"
                )
                print(
                    f"      Difficulty: {first_item['difficulty']:6.2f} → {last_item['difficulty']:6.2f} "
                    f"({difficulty_change:+6.2f})"
                )
                print(
                    f"      Reps:       {first_item['reps']:6d} → {last_item['reps']:6d} "
                    f"({reps_change:+6d})"
                )
                print(
                    f"      Status:     {first_item['mastery_status']} → {last_item['mastery_status']}"
                )
                print()

        # Aggregate statistics
        all_stabilities = []
        all_difficulties = []
        all_reps = []

        for item in last.get("top_items", []):
            all_stabilities.append(item["stability"])
            all_difficulties.append(item["difficulty"])
            all_reps.append(item["reps"])

        if all_stabilities:
            print(f"  Overall Statistics (Session {len(snapshots)}):")
            print(f"    Mean stability:   {statistics.mean(all_stabilities):.2f} days")
            print(f"    Mean difficulty:  {statistics.mean(all_difficulties):.2f}")
            print(f"    Mean reps:        {statistics.mean(all_reps):.1f}")

        print()

    def analyze_mastery_progression(self):
        """Analyze mastery status progression."""
        print("## Mastery Progression\n")

        snapshots = self.stats.get("fsrs_snapshots", [])
        if not snapshots:
            print("  No mastery data\n")
            return

        # Count status transitions
        first = snapshots[0]
        last = snapshots[-1]

        first_statuses = {}
        for item in first.get("top_items", []):
            status = item["mastery_status"]
            first_statuses[status] = first_statuses.get(status, 0) + 1

        last_statuses = {}
        for item in last.get("top_items", []):
            status = item["mastery_status"]
            last_statuses[status] = last_statuses.get(status, 0) + 1

        print(f"  Mastery Status Distribution:\n")
        print(f"    {'Status':<15} {'Session 1':<12} {'Last Session':<15}")
        print(f"    {'-'*15} {'-'*12} {'-'*15}")

        for status in ["new", "learning", "mastered", "fluency_ready"]:
            first_count = first_statuses.get(status, 0)
            last_count = last_statuses.get(status, 0)
            change = last_count - first_count
            change_str = f"({change:+d})" if change != 0 else ""

            print(f"    {status:<15} {first_count:<12} {last_count:<12} {change_str}")

        print()

    def analyze_reliability(self):
        """Analyze system reliability metrics."""
        print("## System Reliability\n")

        total_sessions = self.stats.get("total_sessions", 0)
        total_exercises = self.stats.get("total_exercises", 0)
        errors = self.stats.get("errors", [])

        print(f"  Sessions completed: {total_sessions}/{self.config.get('num_sessions', 0)}")
        print(f"  Total exercises:    {total_exercises}")
        print(f"  Errors encountered: {len(errors)}")

        if total_sessions > 0:
            success_rate = (total_sessions / self.config.get("num_sessions", 1)) * 100
            print(f"  Success rate:       {success_rate:.1f}%")

            if success_rate >= 99:
                print(f"  Status: ✅ Excellent reliability")
            elif success_rate >= 95:
                print(f"  Status: ✓ Good reliability")
            elif success_rate >= 90:
                print(f"  Status: ⚠ Acceptable reliability")
            else:
                print(f"  Status: ❌ Poor reliability")

        print()

    def identify_edge_cases(self):
        """Identify anomalies and edge cases."""
        print("## Edge Cases & Anomalies\n")

        quality_dist = self.stats.get("quality_distribution_overall", {})
        total = sum(quality_dist.values())

        edge_cases = []

        # Check for unexpected quality distributions
        if total > 0:
            q0_pct = (quality_dist.get("0", 0) / total) * 100
            q1_pct = (quality_dist.get("1", 0) / total) * 100
            q5_pct = (quality_dist.get("5", 0) / total) * 100

            if q0_pct > 5:
                edge_cases.append(f"High Q0 rate: {q0_pct:.1f}% (expected <2%)")
            if q1_pct > 10:
                edge_cases.append(f"High Q1 rate: {q1_pct:.1f}% (expected ~4%)")
            if q5_pct > 20:
                edge_cases.append(f"High Q5 rate: {q5_pct:.1f}% (expected ~10%)")

        # Check strand balance convergence
        evolution = self.stats.get("strand_balance_evolution", [])
        if len(evolution) >= 50:
            late_snapshot = evolution[-1]
            target = 0.25

            for strand in ["meaning_input", "meaning_output", "language_focused", "fluency"]:
                value = late_snapshot.get(strand, 0)
                deviation = abs(value - target)
                if deviation > 0.10:  # >10% deviation
                    edge_cases.append(
                        f"Strand '{strand}' not converging: {value:.1%} (target 25%)"
                    )

        # Check errors
        errors = self.stats.get("errors", [])
        if len(errors) > 5:
            edge_cases.append(f"Multiple errors: {len(errors)} failures")

        if edge_cases:
            for case in edge_cases:
                print(f"  ⚠️  {case}")
        else:
            print(f"  ✅ No significant anomalies detected")

        print()

    def print_conclusions(self):
        """Print overall conclusions."""
        print(f"\n{'='*80}")
        print("## CONCLUSIONS")
        print(f"{'='*80}\n")

        # Determine overall health
        issues = []
        successes = []

        # Check success rate
        total_sessions = self.stats.get("total_sessions", 0)
        if total_sessions >= self.config.get("num_sessions", 0) * 0.95:
            successes.append("High session completion rate (>95%)")
        else:
            issues.append("Low session completion rate (<95%)")

        # Check quality distribution
        quality_dist = self.stats.get("quality_distribution_overall", {})
        total = sum(quality_dist.values())
        if total > 0:
            qualities = []
            for q, count in quality_dist.items():
                qualities.extend([int(q)] * count)
            mean_quality = statistics.mean(qualities)

            if 2.5 <= mean_quality <= 3.5:
                successes.append(f"Quality distribution realistic for A2+/B1 (mean {mean_quality:.2f})")
            else:
                issues.append(f"Quality distribution unexpected (mean {mean_quality:.2f})")

        # Check FSRS
        snapshots = self.stats.get("fsrs_snapshots", [])
        if snapshots and len(snapshots) >= 10:
            last = snapshots[-1]
            stabilities = [item["stability"] for item in last.get("top_items", [])]
            if stabilities and statistics.mean(stabilities) > 1.0:
                successes.append("FSRS parameters increasing (items being learned)")
            else:
                issues.append("FSRS parameters not increasing significantly")

        print("✅ Successes:")
        for success in successes:
            print(f"   • {success}")

        if issues:
            print("\n⚠️  Issues Identified:")
            for issue in issues:
                print(f"   • {issue}")
        else:
            print("\n✅ No major issues identified")

        print(f"\n{'='*80}\n")


def main():
    """Analyze results from command line."""
    import argparse

    parser = argparse.ArgumentParser(description="Analyze scale test results")
    parser.add_argument(
        "results_file",
        type=Path,
        help="Path to scale test results JSON file",
    )

    args = parser.parse_args()

    if not args.results_file.exists():
        print(f"Error: File not found: {args.results_file}")
        sys.exit(1)

    analyzer = ResultsAnalyzer(args.results_file)
    analyzer.analyze_all()


if __name__ == "__main__":
    main()
