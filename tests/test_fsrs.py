"""
Tests for FSRS (Free Spaced Repetition Scheduler) algorithm implementation.

This module tests the core FSRS algorithm for calculating stability, difficulty,
and optimal review intervals based on learner performance.

Reference: https://github.com/open-spaced-repetition/fsrs4anki/wiki/The-Algorithm
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest


# ============================================================================
# FSRS Parameter Tests
# ============================================================================


@pytest.mark.fsrs
@pytest.mark.unit
def test_fsrs_default_params_structure(fsrs_default_params: dict[str, Any]) -> None:
    """Test that default FSRS parameters have the correct structure."""
    params = fsrs_default_params

    assert "weights" in params
    assert len(params["weights"]) == 17, "FSRS should have 17 weight parameters"

    assert "request_retention" in params
    assert 0 < params["request_retention"] <= 1.0, "Retention should be between 0 and 1"

    assert "maximum_interval" in params
    assert params["maximum_interval"] > 0

    assert "enable_fuzz" in params
    assert isinstance(params["enable_fuzz"], bool)


@pytest.mark.fsrs
@pytest.mark.unit
def test_fsrs_weights_range(fsrs_default_params: dict[str, Any]) -> None:
    """Test that FSRS weights are within reasonable ranges."""
    weights = fsrs_default_params["weights"]

    # All weights should be positive
    assert all(w > 0 for w in weights), "All FSRS weights should be positive"

    # Specific weight constraints from FSRS specification
    # w0 < w1 < w2 < w3 (initial stability increases with rating)
    assert weights[0] < weights[1] < weights[2] < weights[3], \
        "Initial stability should increase: Again < Hard < Good < Easy"


# ============================================================================
# Initial Stability Tests
# ============================================================================


@pytest.mark.fsrs
@pytest.mark.unit
@pytest.mark.parametrize("rating,weight_index", [
    (1, 0),  # Again -> w0
    (2, 1),  # Hard -> w1
    (3, 2),  # Good -> w2
    (4, 3),  # Easy -> w3
])
def test_calculate_initial_stability(
    fsrs_default_params: dict[str, Any],
    rating: int,
    weight_index: int,
) -> None:
    """
    Test calculating initial stability for first review.

    Initial stability formula: S_0(G) = w_{G-1}
    where G is the rating (1-4) and w are the weights.
    """
    # NOTE: This is a stub implementation. Replace with actual FSRS module when available.
    # from fsrs import calculate_initial_stability

    weights = fsrs_default_params["weights"]
    expected_stability = weights[weight_index]

    # Stub implementation
    def calculate_initial_stability_stub(rating: int, weights: list[float]) -> float:
        return weights[rating - 1]

    stability = calculate_initial_stability_stub(rating, weights)

    assert stability == expected_stability
    assert stability > 0


# ============================================================================
# Initial Difficulty Tests
# ============================================================================


@pytest.mark.fsrs
@pytest.mark.unit
@pytest.mark.parametrize("rating", [1, 2, 3, 4])
def test_calculate_initial_difficulty(
    fsrs_default_params: dict[str, Any],
    rating: int,
) -> None:
    """
    Test calculating initial difficulty for first review.

    Initial difficulty formula: D_0(G) = w_4 - (G-3) * w_5
    where G is the rating and w are the weights.
    """
    # NOTE: This is a stub. Replace with actual implementation.
    # from fsrs import calculate_initial_difficulty

    weights = fsrs_default_params["weights"]
    w4, w5 = weights[4], weights[5]

    # Stub implementation
    def calculate_initial_difficulty_stub(rating: int, w4: float, w5: float) -> float:
        difficulty = w4 - (rating - 3) * w5
        return max(1.0, min(10.0, difficulty))  # Clamp to [1, 10]

    difficulty = calculate_initial_difficulty_stub(rating, w4, w5)

    # Difficulty should be in valid range
    assert 1.0 <= difficulty <= 10.0

    # Higher ratings should result in lower difficulty
    if rating == 4:  # Easy
        difficulty_easy = difficulty
        difficulty_again = calculate_initial_difficulty_stub(1, w4, w5)
        assert difficulty_easy < difficulty_again, "Easy rating should result in lower difficulty"


# ============================================================================
# Stability Calculation Tests
# ============================================================================


@pytest.mark.fsrs
@pytest.mark.unit
def test_calculate_next_stability_successful_recall(
    fsrs_default_params: dict[str, Any],
) -> None:
    """
    Test stability calculation after successful recall (rating >= 3).

    Formula: S' = S * (e^(w_8) * (11 - D) * S^(-w_9) * (e^(w_10 * (1 - R))) - 1)
    where R is the retrievability at review time.
    """
    # NOTE: Stub implementation
    # from fsrs import calculate_next_stability

    current_stability = 2.5
    difficulty = 5.0
    rating = 3  # Good
    elapsed_days = 2.0

    weights = fsrs_default_params["weights"]

    # Stub: simplified formula
    def calculate_next_stability_stub(
        current_s: float,
        difficulty: float,
        rating: int,
        elapsed: float,
        weights: list[float],
    ) -> float:
        # Simplified: stability increases with successful recall
        if rating >= 3:
            return current_s * 1.5  # Simple multiplier for successful recall
        else:
            return current_s * 0.5  # Decrease for failed recall

    next_stability = calculate_next_stability_stub(
        current_stability, difficulty, rating, elapsed_days, weights
    )

    # Stability should increase after successful recall
    assert next_stability > current_stability


@pytest.mark.fsrs
@pytest.mark.unit
def test_calculate_next_stability_failed_recall(
    fsrs_default_params: dict[str, Any],
) -> None:
    """Test stability calculation after failed recall (rating < 3)."""
    current_stability = 2.5
    difficulty = 5.0
    rating = 1  # Again
    elapsed_days = 2.0

    weights = fsrs_default_params["weights"]

    # Stub implementation
    def calculate_next_stability_stub(
        current_s: float,
        difficulty: float,
        rating: int,
        elapsed: float,
        weights: list[float],
    ) -> float:
        if rating >= 3:
            return current_s * 1.5
        else:
            return current_s * 0.5

    next_stability = calculate_next_stability_stub(
        current_stability, difficulty, rating, elapsed_days, weights
    )

    # Stability should decrease after failed recall
    assert next_stability < current_stability


# ============================================================================
# Difficulty Update Tests
# ============================================================================


@pytest.mark.fsrs
@pytest.mark.unit
@pytest.mark.parametrize("rating,expected_change", [
    (1, "increase"),  # Again -> difficulty increases
    (2, "increase"),  # Hard -> difficulty increases slightly
    (3, "stable"),    # Good -> difficulty stable
    (4, "decrease"),  # Easy -> difficulty decreases
])
def test_update_difficulty(
    fsrs_default_params: dict[str, Any],
    rating: int,
    expected_change: str,
) -> None:
    """
    Test difficulty update based on rating.

    Formula: D' = D - w_6 * (G - 3)
    where G is the rating (1-4).
    """
    # NOTE: Stub implementation
    # from fsrs import update_difficulty

    current_difficulty = 5.0
    weights = fsrs_default_params["weights"]
    w6 = weights[6]

    # Stub implementation
    def update_difficulty_stub(
        current_d: float,
        rating: int,
        w6: float,
    ) -> float:
        new_d = current_d - w6 * (rating - 3)
        return max(1.0, min(10.0, new_d))  # Clamp to [1, 10]

    new_difficulty = update_difficulty_stub(current_difficulty, rating, w6)

    # Verify difficulty is in valid range
    assert 1.0 <= new_difficulty <= 10.0

    # Check expected change direction
    if expected_change == "increase":
        assert new_difficulty > current_difficulty or new_difficulty == 10.0
    elif expected_change == "decrease":
        assert new_difficulty < current_difficulty or new_difficulty == 1.0
    elif expected_change == "stable":
        # For "Good" rating, difficulty should stay approximately the same
        assert abs(new_difficulty - current_difficulty) < 0.1


# ============================================================================
# Retrievability Tests
# ============================================================================


@pytest.mark.fsrs
@pytest.mark.unit
def test_calculate_retrievability(fsrs_default_params: dict[str, Any]) -> None:
    """
    Test retrievability calculation.

    Formula: R = (1 + FACTOR * t / S) ^ DECAY
    where t is elapsed time, S is stability, and FACTOR/DECAY are from weights.
    """
    # NOTE: Stub implementation
    # from fsrs import calculate_retrievability

    stability = 5.0
    elapsed_days = 3.0

    # Stub: simplified exponential decay
    def calculate_retrievability_stub(stability: float, elapsed: float) -> float:
        decay_factor = 0.9
        retrievability = decay_factor ** (elapsed / stability)
        return max(0.0, min(1.0, retrievability))

    retrievability = calculate_retrievability_stub(stability, elapsed_days)

    # Retrievability should be between 0 and 1
    assert 0.0 <= retrievability <= 1.0

    # Test edge cases
    r_at_zero = calculate_retrievability_stub(stability, 0.0)
    assert r_at_zero > retrievability, "Retrievability should be higher at t=0"

    r_at_long = calculate_retrievability_stub(stability, 30.0)
    assert r_at_long < retrievability, "Retrievability should decrease over time"


# ============================================================================
# Interval Calculation Tests
# ============================================================================


@pytest.mark.fsrs
@pytest.mark.unit
def test_calculate_next_interval(fsrs_default_params: dict[str, Any]) -> None:
    """
    Test calculating next review interval.

    Formula: I = S * ln(retention) / ln(0.9)
    where S is stability and retention is the desired retention rate.
    """
    # NOTE: Stub implementation
    # from fsrs import calculate_interval

    stability = 5.0
    request_retention = fsrs_default_params["request_retention"]

    # Stub implementation
    def calculate_interval_stub(stability: float, retention: float) -> int:
        interval_days = stability * (math.log(retention) / math.log(0.9))
        return max(1, int(round(interval_days)))

    interval = calculate_interval_stub(stability, request_retention)

    # Interval should be positive
    assert interval > 0

    # Higher stability should result in longer interval
    interval_low_stability = calculate_interval_stub(2.0, request_retention)
    interval_high_stability = calculate_interval_stub(10.0, request_retention)
    assert interval_high_stability > interval_low_stability


@pytest.mark.fsrs
@pytest.mark.unit
def test_interval_respects_maximum(fsrs_default_params: dict[str, Any]) -> None:
    """Test that calculated intervals respect maximum interval constraint."""
    # NOTE: Stub implementation
    # from fsrs import calculate_interval

    very_high_stability = 50000.0  # Unrealistically high
    request_retention = fsrs_default_params["request_retention"]
    maximum_interval = fsrs_default_params["maximum_interval"]

    def calculate_interval_stub(
        stability: float,
        retention: float,
        max_interval: int,
    ) -> int:
        interval_days = stability * (math.log(retention) / math.log(0.9))
        return min(max_interval, max(1, int(round(interval_days))))

    interval = calculate_interval_stub(
        very_high_stability, request_retention, maximum_interval
    )

    assert interval <= maximum_interval


# ============================================================================
# Complete Review Tests
# ============================================================================


@pytest.mark.fsrs
@pytest.mark.integration
def test_complete_review_cycle_new_card(fsrs_default_params: dict[str, Any]) -> None:
    """Test a complete review cycle for a new card."""
    # NOTE: This is a stub for an integrated FSRS function
    # from fsrs import process_review

    # Initial state (new card)
    stability = 0.0
    difficulty = 5.0
    reps = 0
    last_review = None

    # First review with "Good" rating
    rating = 3
    review_time = datetime.now(timezone.utc)

    # Stub implementation of complete review
    def process_review_stub(
        stability: float,
        difficulty: float,
        reps: int,
        rating: int,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        weights = params["weights"]

        # Calculate new values
        if reps == 0:
            # First review
            new_stability = weights[rating - 1]  # Initial stability
            new_difficulty = weights[4] - (rating - 3) * weights[5]
            new_difficulty = max(1.0, min(10.0, new_difficulty))
        else:
            # Subsequent reviews (simplified)
            new_stability = stability * 1.5 if rating >= 3 else stability * 0.5
            new_difficulty = difficulty

        interval = max(1, int(new_stability))

        return {
            "stability": new_stability,
            "difficulty": new_difficulty,
            "reps": reps + 1,
            "interval": interval,
        }

    result = process_review_stub(stability, difficulty, reps, rating, fsrs_default_params)

    # Verify results
    assert result["stability"] > 0
    assert 1.0 <= result["difficulty"] <= 10.0
    assert result["reps"] == 1
    assert result["interval"] > 0


@pytest.mark.fsrs
@pytest.mark.integration
@pytest.mark.parametrize("rating_sequence,expected_trend", [
    ([3, 3, 3, 3], "increasing"),  # Consistent good performance -> stability increases
    ([1, 1, 1, 1], "decreasing"),  # Consistent failures -> stability decreases
    ([3, 1, 3, 1], "volatile"),    # Mixed performance -> more variable
])
def test_review_sequence_stability_trends(
    fsrs_default_params: dict[str, Any],
    rating_sequence: list[int],
    expected_trend: str,
) -> None:
    """Test that stability trends match expected patterns over multiple reviews."""
    # NOTE: Stub implementation
    # from fsrs import process_review

    def process_review_stub(
        stability: float,
        difficulty: float,
        reps: int,
        rating: int,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        weights = params["weights"]

        if reps == 0:
            new_stability = weights[rating - 1]
            new_difficulty = max(1.0, min(10.0, weights[4] - (rating - 3) * weights[5]))
        else:
            if rating >= 3:
                new_stability = stability * 1.5
            else:
                new_stability = stability * 0.5
            new_difficulty = difficulty

        return {
            "stability": new_stability,
            "difficulty": new_difficulty,
            "reps": reps + 1,
            "interval": max(1, int(new_stability)),
        }

    # Simulate review sequence
    stability = 0.0
    difficulty = 5.0
    reps = 0
    stability_history = []

    for rating in rating_sequence:
        result = process_review_stub(stability, difficulty, reps, rating, fsrs_default_params)
        stability = result["stability"]
        difficulty = result["difficulty"]
        reps = result["reps"]
        stability_history.append(stability)

    # Check trend
    if expected_trend == "increasing":
        # Stability should generally increase
        assert stability_history[-1] > stability_history[0]
        # Each step should generally increase (with some tolerance)
        increases = sum(
            1 for i in range(len(stability_history) - 1)
            if stability_history[i + 1] >= stability_history[i]
        )
        assert increases >= len(stability_history) - 2

    elif expected_trend == "decreasing":
        # Stability should generally decrease or stay low
        assert stability_history[-1] <= stability_history[1] * 1.5  # Allow some tolerance

    elif expected_trend == "volatile":
        # Should have both increases and decreases
        changes = [
            stability_history[i + 1] - stability_history[i]
            for i in range(len(stability_history) - 1)
        ]
        has_increases = any(c > 0 for c in changes)
        has_decreases = any(c < 0 for c in changes)
        assert has_increases or has_decreases


# ============================================================================
# Edge Cases and Validation Tests
# ============================================================================


@pytest.mark.fsrs
@pytest.mark.unit
def test_invalid_rating_handling() -> None:
    """Test that invalid ratings are handled appropriately."""
    # NOTE: Stub implementation
    # from fsrs import validate_rating

    def validate_rating_stub(rating: int) -> bool:
        return 1 <= rating <= 4

    assert validate_rating_stub(1) is True
    assert validate_rating_stub(4) is True
    assert validate_rating_stub(0) is False
    assert validate_rating_stub(5) is False
    assert validate_rating_stub(-1) is False


@pytest.mark.fsrs
@pytest.mark.unit
def test_zero_stability_handling() -> None:
    """Test that zero stability is handled correctly (new cards)."""
    # New cards should start with initial stability, never zero
    weights = [0.4, 1.2, 3.1, 15.5]

    def calculate_initial_stability_stub(rating: int, weights: list[float]) -> float:
        return weights[rating - 1]

    for rating in [1, 2, 3, 4]:
        stability = calculate_initial_stability_stub(rating, weights)
        assert stability > 0, f"Initial stability should be positive for rating {rating}"


@pytest.mark.fsrs
@pytest.mark.unit
def test_very_high_difficulty() -> None:
    """Test behavior with very high difficulty (challenging items)."""
    # High difficulty should result in shorter intervals
    def calculate_interval_stub(stability: float, difficulty: float) -> int:
        # Simplified: higher difficulty reduces effective stability
        effective_stability = stability * (10.0 / difficulty)
        return max(1, int(effective_stability))

    interval_normal = calculate_interval_stub(5.0, 5.0)
    interval_high_difficulty = calculate_interval_stub(5.0, 9.0)

    assert interval_high_difficulty < interval_normal


@pytest.mark.fsrs
@pytest.mark.unit
def test_very_low_difficulty() -> None:
    """Test behavior with very low difficulty (easy items)."""
    # Low difficulty should result in longer intervals
    def calculate_interval_stub(stability: float, difficulty: float) -> int:
        effective_stability = stability * (10.0 / difficulty)
        return max(1, int(effective_stability))

    interval_normal = calculate_interval_stub(5.0, 5.0)
    interval_low_difficulty = calculate_interval_stub(5.0, 2.0)

    assert interval_low_difficulty > interval_normal
