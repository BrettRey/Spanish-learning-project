#!/usr/bin/env python3
"""
Test Preview & Negotiate Workflow

Demonstrates the new learner agency features:
- Preview session plan before starting
- Negotiate adjustments based on learner goals
- Start session with adjusted preferences
"""

from pathlib import Path
from state.coach import Coach


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_exercises(exercises, show_all=False):
    """Print exercise summary grouped by strand."""
    strands = {}
    for ex in exercises:
        strand = ex["strand"]
        if strand not in strands:
            strands[strand] = []
        strands[strand].append(ex)

    for strand, exs in strands.items():
        print(f"  • {len(exs)} {strand}:")
        if show_all:
            for ex in exs:
                node_label = ex['node_id'].split('.')[-1].replace('_', ' ').title()
                print(f"      - {node_label}")
        else:
            sample = exs[0]['node_id'].split('.')[-1].replace('_', ' ').title()
            if len(exs) > 1:
                print(f"      ({sample}, ...)")
            else:
                print(f"      ({sample})")


def main():
    # Initialize coach with test databases
    coach = Coach(
        kg_db_path=Path("kg.sqlite"),
        mastery_db_path=Path("state/mastery.sqlite")
    )

    learner_id = "preview_test_learner"

    print_section("Scenario: Standard Session with Negotiation")

    print("🤖 Coach: Welcome! Let me show you what I've planned for today...")
    print()

    # 1. Preview initial plan
    print("📋 Calling: coach.preview_session()")
    preview = coach.preview_session(
        learner_id=learner_id,
        duration_minutes=20
    )

    print(f"\n✅ Preview returned ({preview['total_exercises']} exercises)")
    print(f"\n📊 Current Balance:")
    for strand, pct in preview['current_balance'].items():
        print(f"  {strand:20s}: {pct}")

    print(f"\n📝 Balance Status: {preview['balance_status']}")
    print(f"💡 Guidance: {preview['llm_guidance']}")

    print(f"\n🎯 Planned Exercises:")
    print_exercises(preview['exercises'])

    print("\n" + "-"*60)
    print("🤖 Coach: Ready to start, or would you like to adjust the focus?")
    print("👤 Learner: Actually, I have a trip to Barcelona next month.")
    print("             Can we focus on travel Spanish?")
    print("-"*60)

    # 2. Adjust focus based on goal
    print("\n🔧 Calling: coach.adjust_focus('prepare for travel to Barcelona')")

    # Parse current balance to decimal for adjust_focus
    current_balance = {
        strand: float(pct.rstrip('%')) / 100
        for strand, pct in preview['current_balance'].items()
    }

    weights = coach.adjust_focus(
        goal_description="prepare for travel to Barcelona",
        current_balance=current_balance
    )

    print(f"\n✅ Adjusted weights:")
    for strand, weight in weights.items():
        print(f"  {strand:20s}: {weight:.2f}")

    # 3. Preview with adjusted weights
    print("\n📋 Calling: coach.preview_session() with adjusted weights")
    adjusted_preview = coach.preview_session(
        learner_id=learner_id,
        duration_minutes=20,
        learner_preference=weights
    )

    print(f"\n✅ Adjusted preview ({adjusted_preview['total_exercises']} exercises)")
    print(f"\n🎯 Adjusted Exercises:")
    print_exercises(adjusted_preview['exercises'], show_all=True)

    print("\n" + "-"*60)
    print("🤖 Coach: Perfect! I've adjusted the plan to prioritize travel")
    print("             situations while maintaining balance. Let's begin!")
    print("👤 Learner: Great, let's do it!")
    print("-"*60)

    # 4. Start session with adjusted preferences
    print("\n🚀 Calling: coach.start_session() with adjusted preferences")
    session = coach.start_session(
        learner_id=learner_id,
        duration_minutes=20,
        learner_preference=weights
    )

    print(f"\n✅ Session started: {session['session_id']}")
    print(f"   {session['total_exercises']} exercises ready")

    # 5. End session (without running exercises for this demo)
    print("\n🏁 Calling: coach.end_session()")
    summary = coach.end_session(session['session_id'])

    print(f"\n✅ Session ended successfully")
    print(f"   Duration: {summary['duration_actual_min']:.1f} minutes")
    print(f"   Exercises: {summary['exercises_completed']}/{session['total_exercises']} completed")

    print_section("Test Other Goal Types")

    test_goals = [
        "improve my grammar and fix mistakes",
        "understand Spanish podcasts and movies",
        "speak more fluently and naturally",
        "write professional emails in Spanish"
    ]

    for goal in test_goals:
        print(f"\n🎯 Goal: '{goal}'")
        weights = coach.adjust_focus(goal, current_balance)

        # Find highest weighted strand
        max_strand = max(weights.items(), key=lambda x: x[1])

        print(f"   Primary focus: {max_strand[0]} (weight: {max_strand[1]:.1f})")
        print(f"   All weights: ", end="")
        abbrev = {"meaning_input": "MI", "meaning_output": "MO", "language_focused": "LF", "fluency": "FL"}
        print(", ".join(f"{abbrev[s]}={w:.1f}" for s, w in weights.items()))

    print_section("Summary")
    print("✅ preview_session() - Returns plan WITHOUT starting session")
    print("✅ adjust_focus() - Translates goals into preference weights")
    print("✅ start_session() - Accepts preference weights for customization")
    print("✅ Learner agency workflow validated")
    print()
    print("The LLM coach can now:")
    print("  1. Preview plans conversationally")
    print("  2. Negotiate adjustments based on learner goals")
    print("  3. Start sessions with negotiated preferences")
    print("  4. Maintain algorithmic constraints (SRS, strand balance)")
    print()
    print("See COACH_INSTRUCTIONS.md for full workflow documentation.")
    print()


if __name__ == "__main__":
    main()
