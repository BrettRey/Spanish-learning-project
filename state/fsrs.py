"""
Free Spaced Repetition Scheduler (FSRS) Algorithm Implementation.

This module implements the FSRS algorithm for calculating optimal review schedules
based on memory science and spaced repetition principles.

References:
- FSRS Paper: https://github.com/open-spaced-repetition/fsrs4anki/wiki/The-Algorithm
- Original Research: Piotr Wozniak's SM-2 algorithm and subsequent improvements
- FSRS is an open-source alternative to SuperMemo's SM-2 with better predictive accuracy

Key Concepts:
- Stability (S): Estimated time (in days) for retrievability to decay to 90%
- Difficulty (D): Intrinsic difficulty of the item (0-10 scale)
- Retrievability (R): Probability of successful recall (0-1 scale)
- Quality (Q): User's self-rated recall quality (0-5 scale)

FSRS Quality Scale:
- 0: Complete blackout (no memory)
- 1: Incorrect response, but correct answer seemed familiar
- 2: Incorrect response, but correct answer seemed easy to recall
- 3: Correct response, but required significant difficulty to recall
- 4: Correct response, with some hesitation
- 5: Perfect response, immediate recall
"""

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Tuple


# FSRS Default Parameters (optimized from research data)
# These can be fine-tuned per learner using optimization algorithms
DEFAULT_W = [
    0.4,    # w[0]: initial stability for Q=1
    0.6,    # w[1]: initial stability for Q=2
    2.4,    # w[2]: initial stability for Q=3
    5.8,    # w[3]: initial stability for Q=4
    4.93,   # w[4]: difficulty decay rate
    0.94,   # w[5]: stability increase rate for easy recalls
    0.86,   # w[6]: stability increase rate for good recalls
    0.01,   # w[7]: stability increase rate for hard recalls
    1.49,   # w[8]: stability decay rate for lapses
    0.14,   # w[9]: initial difficulty for Q=1
    0.94,   # w[10]: difficulty weight factor
    2.18,   # w[11]: stability power factor
    0.05,   # w[12]: difficulty update rate
    0.34,   # w[13]: retrievability threshold for hard items
    1.26,   # w[14]: retrievability decay factor
    0.29,   # w[15]: stability increase bonus
    2.61,   # w[16]: stability multiplier
]


@dataclass
class ReviewCard:
    """Represents a card's state in the SRS system."""
    stability: float  # S: time for retrievability to decay to 90% (in days)
    difficulty: float  # D: intrinsic difficulty (0-10 scale)
    reps: int  # Number of reviews
    last_review: datetime | None = None


@dataclass
class ReviewResult:
    """Result of a review operation."""
    stability: float
    difficulty: float
    next_review_date: datetime
    retrievability: float  # Probability of recall at time of review


def initial_stability(quality: int, w: list[float] = DEFAULT_W) -> float:
    """
    Calculate initial stability for a new card based on first review quality.

    For new cards (reps=0), stability is determined by the quality of the first review.

    Args:
        quality: Review quality (0-5 scale)
        w: FSRS weight parameters

    Returns:
        Initial stability in days

    Raises:
        ValueError: If quality is not in range 0-5
    """
    if not 0 <= quality <= 5:
        raise ValueError(f"Quality must be in range 0-5, got {quality}")

    # For quality 0 (complete failure), use minimal stability
    if quality == 0:
        return 0.1

    # For quality 1-2, use w[0] with quality adjustment
    if quality <= 2:
        return w[0] * (quality / 2)

    # For quality 3, use w[2]
    if quality == 3:
        return w[2]

    # For quality 4-5, interpolate between w[2] and w[3]
    return w[2] + (w[3] - w[2]) * (quality - 3) / 2


def initial_difficulty(quality: int, w: list[float] = DEFAULT_W) -> float:
    """
    Calculate initial difficulty for a new card based on first review quality.

    Difficulty represents how hard an item is to remember. Lower quality ratings
    result in higher difficulty scores.

    Args:
        quality: Review quality (0-5 scale)
        w: FSRS weight parameters

    Returns:
        Initial difficulty (0-10 scale)

    Raises:
        ValueError: If quality is not in range 0-5
    """
    if not 0 <= quality <= 5:
        raise ValueError(f"Quality must be in range 0-5, got {quality}")

    # Map quality (0-5) to difficulty (0-10)
    # Lower quality = higher difficulty
    difficulty = w[4] - w[10] * (quality - 3)

    # Clamp to valid range
    return max(1.0, min(10.0, difficulty))


def calculate_retrievability(
    elapsed_days: float,
    stability: float,
    w: list[float] = DEFAULT_W
) -> float:
    """
    Calculate the probability of successful recall (retrievability).

    Retrievability decays exponentially based on elapsed time and stability.
    At elapsed_days = stability, retrievability = 0.9 (by definition).

    Args:
        elapsed_days: Days since last review
        stability: Current stability in days
        w: FSRS weight parameters

    Returns:
        Retrievability (probability of recall, 0-1 scale)
    """
    if stability <= 0:
        return 0.0

    # FSRS retrievability formula: R = exp(ln(0.9) * elapsed_days / stability)
    # This ensures R = 0.9 when elapsed_days = stability
    retrievability = math.exp(math.log(0.9) * elapsed_days / stability)

    return max(0.0, min(1.0, retrievability))


def update_stability(
    current_stability: float,
    difficulty: float,
    quality: int,
    retrievability: float,
    w: list[float] = DEFAULT_W
) -> float:
    """
    Calculate new stability after a review.

    The new stability depends on:
    - Current stability
    - Item difficulty
    - Review quality (how well the user recalled)
    - Retrievability at time of review

    Args:
        current_stability: Current stability in days
        difficulty: Current difficulty (0-10 scale)
        quality: Review quality (0-5 scale)
        retrievability: Retrievability at time of review (0-1 scale)
        w: FSRS weight parameters

    Returns:
        New stability in days

    Raises:
        ValueError: If quality is not in range 0-5
    """
    if not 0 <= quality <= 5:
        raise ValueError(f"Quality must be in range 0-5, got {quality}")

    # For failed recalls (quality < 3), stability decreases
    if quality < 3:
        # Lapse: new stability is reduced based on difficulty
        new_stability = w[11] * math.pow(difficulty, -w[12]) * (
            math.pow(current_stability + 1, w[13]) - 1
        ) * math.exp((1 - retrievability) * w[14])

        return max(0.1, new_stability)

    # For successful recalls (quality >= 3), stability increases
    # Success factor depends on quality
    if quality == 3:
        success_factor = w[7]  # Hard
    elif quality == 4:
        success_factor = w[6]  # Good
    else:  # quality == 5
        success_factor = w[5]  # Easy

    # Calculate stability increase
    # Higher retrievability at review time = bigger stability increase
    stability_increase = (
        w[16] *
        math.pow(difficulty, -w[12]) *
        (math.pow(current_stability, w[11]) - 1) *
        math.exp((1 - retrievability) * w[14])
    )

    new_stability = current_stability * (
        1 +
        math.exp(w[15]) *
        (11 - difficulty) *
        math.pow(current_stability, -w[13]) *
        (math.exp((1 - retrievability) * w[14]) - 1) *
        success_factor
    )

    return max(0.1, new_stability)


def update_difficulty(
    current_difficulty: float,
    quality: int,
    w: list[float] = DEFAULT_W
) -> float:
    """
    Calculate new difficulty after a review.

    Difficulty changes based on review quality:
    - Failed recalls (quality < 3) increase difficulty
    - Successful recalls (quality >= 3) decrease difficulty
    - Changes are gradual to avoid over-correction

    Args:
        current_difficulty: Current difficulty (0-10 scale)
        quality: Review quality (0-5 scale)
        w: FSRS weight parameters

    Returns:
        New difficulty (0-10 scale)

    Raises:
        ValueError: If quality is not in range 0-5
    """
    if not 0 <= quality <= 5:
        raise ValueError(f"Quality must be in range 0-5, got {quality}")

    # Calculate difficulty change based on quality
    # quality < 3: difficulty increases
    # quality >= 3: difficulty decreases
    mean_quality = 3.0
    difficulty_delta = w[12] * (quality - mean_quality)

    # Update difficulty with decay factor
    new_difficulty = current_difficulty - difficulty_delta

    # Clamp to valid range
    return max(1.0, min(10.0, new_difficulty))


def calculate_next_review_date(
    stability: float,
    current_time: datetime | None = None,
    request_retention: float = 0.9
) -> datetime:
    """
    Calculate the next optimal review date based on stability.

    The next review is scheduled when retrievability is expected to drop
    to the requested retention level (default 90%).

    Args:
        stability: Current stability in days
        current_time: Current datetime (default: now)
        request_retention: Target retention level (default: 0.9)

    Returns:
        Datetime for next review

    Raises:
        ValueError: If request_retention is not in range (0, 1)
    """
    if not 0 < request_retention < 1:
        raise ValueError(f"request_retention must be in range (0, 1), got {request_retention}")

    if current_time is None:
        current_time = datetime.now()

    # Calculate interval: solve R = exp(ln(retention) * t / S) for t
    # t = S * ln(retention) / ln(0.9)
    interval_days = stability * math.log(request_retention) / math.log(0.9)

    # Ensure minimum interval of 1 day
    interval_days = max(1.0, interval_days)

    return current_time + timedelta(days=interval_days)


def review_card(
    card: ReviewCard,
    quality: int,
    review_time: datetime | None = None,
    w: list[float] = DEFAULT_W
) -> Tuple[ReviewCard, ReviewResult]:
    """
    Process a card review and update its parameters.

    This is the main function that orchestrates the FSRS algorithm:
    1. Calculate retrievability at review time
    2. Update stability based on review quality
    3. Update difficulty based on review quality
    4. Calculate next review date

    Args:
        card: Current card state
        quality: Review quality (0-5 scale)
        review_time: Time of review (default: now)
        w: FSRS weight parameters

    Returns:
        Tuple of (updated_card, review_result)

    Raises:
        ValueError: If quality is not in range 0-5

    Example:
        >>> card = ReviewCard(stability=2.5, difficulty=5.0, reps=3)
        >>> updated_card, result = review_card(card, quality=4)
        >>> print(f"Next review in {(result.next_review_date - datetime.now()).days} days")
    """
    if not 0 <= quality <= 5:
        raise ValueError(f"Quality must be in range 0-5, got {quality}")

    if review_time is None:
        review_time = datetime.now()

    # Handle new cards (first review)
    if card.reps == 0:
        new_stability = initial_stability(quality, w)
        new_difficulty = initial_difficulty(quality, w)
        retrievability = 1.0  # No decay yet
    else:
        # Calculate elapsed time since last review
        if card.last_review is None:
            elapsed_days = 0.0
        else:
            elapsed_days = (review_time - card.last_review).total_seconds() / 86400

        # Calculate retrievability at review time
        retrievability = calculate_retrievability(elapsed_days, card.stability, w)

        # Update parameters based on review
        new_stability = update_stability(
            card.stability, card.difficulty, quality, retrievability, w
        )
        new_difficulty = update_difficulty(card.difficulty, quality, w)

    # Calculate next review date
    next_review = calculate_next_review_date(new_stability, review_time)

    # Create updated card
    updated_card = ReviewCard(
        stability=new_stability,
        difficulty=new_difficulty,
        reps=card.reps + 1,
        last_review=review_time
    )

    # Create review result
    result = ReviewResult(
        stability=new_stability,
        difficulty=new_difficulty,
        next_review_date=next_review,
        retrievability=retrievability
    )

    return updated_card, result


def get_review_interval_days(stability: float, request_retention: float = 0.9) -> float:
    """
    Calculate the interval in days for a given stability and retention target.

    This is a convenience function for understanding review schedules.

    Args:
        stability: Current stability in days
        request_retention: Target retention level (default: 0.9)

    Returns:
        Interval in days until next review

    Example:
        >>> interval = get_review_interval_days(stability=5.0, request_retention=0.9)
        >>> print(f"Review in {interval:.1f} days")
    """
    return stability * math.log(request_retention) / math.log(0.9)
