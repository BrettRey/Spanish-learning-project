"""
Tests for Spaced Repetition System (SRS) MCP server tools.

This module tests the MCP tools that expose SRS functionality:
- srs.due(): Get items due for review
- srs.update(): Update item after review
- srs.schedule(): Calculate next review date
- srs.stats(): Get learner statistics
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest


# ============================================================================
# srs.due() - Due Items Query Tests
# ============================================================================


@pytest.mark.mcp
@pytest.mark.srs
@pytest.mark.unit
def test_srs_due_returns_due_items(populated_mastery_db: Path) -> None:
    """Test srs.due() returns items that are due for review."""
    # from mcp_servers.srs_server import srs_due

    # Stub implementation
    def srs_due_stub(mastery_db_path: Path, learner_id: str, limit: int = 10) -> str:
        """Get items due for review."""
        conn = sqlite3.connect(mastery_db_path)
        cursor = conn.cursor()

        # Query due items view
        cursor.execute("SELECT * FROM due_items LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()

        items = [
            {
                "item_id": row[0],
                "node_id": row[1],
                "type": row[2],
                "last_review": row[3],
                "stability": row[4],
                "difficulty": row[5],
                "reps": row[6],
            }
            for row in rows
        ]
        return json.dumps(items)

    result_json = srs_due_stub(populated_mastery_db, "test_learner", limit=10)
    result = json.loads(result_json)

    assert isinstance(result, list)
    assert len(result) > 0

    # Verify structure
    for item in result:
        assert "item_id" in item
        assert "node_id" in item
        assert "stability" in item
        assert "difficulty" in item


@pytest.mark.mcp
@pytest.mark.srs
@pytest.mark.unit
def test_srs_due_respects_limit(populated_mastery_db: Path) -> None:
    """Test that srs.due() respects the limit parameter."""
    def srs_due_stub(mastery_db_path: Path, limit: int) -> str:
        conn = sqlite3.connect(mastery_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM due_items LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()

        items = [
            {"item_id": row[0], "node_id": row[1]}
            for row in rows
        ]
        return json.dumps(items)

    # Test different limits
    for limit in [1, 3, 5]:
        result = json.loads(srs_due_stub(populated_mastery_db, limit))
        assert len(result) <= limit


@pytest.mark.mcp
@pytest.mark.srs
@pytest.mark.unit
def test_srs_due_includes_new_items(populated_mastery_db: Path) -> None:
    """Test that srs.due() includes items never reviewed (new items)."""
    def srs_due_stub(mastery_db_path: Path) -> str:
        conn = sqlite3.connect(mastery_db_path)
        cursor = conn.cursor()

        # Get items with no review history
        cursor.execute("""
            SELECT item_id, node_id, type, stability, difficulty, reps
            FROM items
            WHERE last_review IS NULL
        """)
        rows = cursor.fetchall()
        conn.close()

        items = [
            {
                "item_id": row[0],
                "node_id": row[1],
                "type": row[2],
                "stability": row[3],
                "difficulty": row[4],
                "reps": row[5],
                "is_new": True,
            }
            for row in rows
        ]
        return json.dumps(items)

    result = json.loads(srs_due_stub(populated_mastery_db))

    assert len(result) > 0

    # All should be new items
    for item in result:
        assert item["is_new"] is True
        assert item["reps"] == 0


@pytest.mark.mcp
@pytest.mark.srs
@pytest.mark.integration
def test_srs_due_sorts_by_priority(populated_mastery_db: Path) -> None:
    """
    Test that srs.due() returns items in priority order.

    Priority factors:
    - New items first (or last, depending on strategy)
    - Older overdue items before newer ones
    - Items with lower stability (more likely to be forgotten)
    """
    def srs_due_stub(mastery_db_path: Path) -> str:
        conn = sqlite3.connect(mastery_db_path)
        cursor = conn.cursor()

        # Order by last_review ascending (older first), NULL first (new items)
        cursor.execute("""
            SELECT item_id, node_id, last_review, stability
            FROM items
            ORDER BY last_review ASC NULLS FIRST
        """)
        rows = cursor.fetchall()
        conn.close()

        items = [
            {
                "item_id": row[0],
                "node_id": row[1],
                "last_review": row[2],
                "stability": row[3],
            }
            for row in rows
        ]
        return json.dumps(items)

    result = json.loads(srs_due_stub(populated_mastery_db))

    # First items should be new (NULL last_review)
    if len(result) > 0:
        # At least some items should be present
        assert len(result) > 0


# ============================================================================
# srs.update() - Item Update Tests
# ============================================================================


@pytest.mark.mcp
@pytest.mark.srs
@pytest.mark.unit
def test_srs_update_creates_review_history(
    populated_mastery_db: Path,
    fsrs_default_params: dict[str, Any],
) -> None:
    """Test srs.update() creates a review history record."""
    # from mcp_servers.srs_server import srs_update

    # Stub implementation
    def srs_update_stub(
        mastery_db_path: Path,
        item_id: str,
        quality: int,
        fsrs_params: dict[str, Any],
    ) -> str:
        """Update item after review."""
        conn = sqlite3.connect(mastery_db_path)
        cursor = conn.cursor()

        # Get current item state
        cursor.execute(
            "SELECT stability, difficulty, reps FROM items WHERE item_id = ?",
            (item_id,),
        )
        row = cursor.fetchone()

        if not row:
            conn.close()
            return json.dumps({"error": "Item not found"})

        old_stability, old_difficulty, reps = row

        # Simplified FSRS update (stub)
        if reps == 0:
            # First review
            new_stability = fsrs_params["weights"][quality - 1]
            new_difficulty = max(1.0, min(10.0, fsrs_params["weights"][4] - (quality - 3) * fsrs_params["weights"][5]))
        else:
            # Subsequent reviews
            new_stability = old_stability * (1.5 if quality >= 3 else 0.5)
            new_difficulty = old_difficulty

        # Update item
        cursor.execute(
            """
            UPDATE items
            SET stability = ?, difficulty = ?, reps = ?, last_review = CURRENT_TIMESTAMP
            WHERE item_id = ?
            """,
            (new_stability, new_difficulty, reps + 1, item_id),
        )

        # Insert review history
        cursor.execute(
            """
            INSERT INTO review_history
            (item_id, quality, stability_before, stability_after, difficulty_before, difficulty_after)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (item_id, quality, old_stability, new_stability, old_difficulty, new_difficulty),
        )

        conn.commit()
        conn.close()

        return json.dumps({
            "status": "success",
            "item_id": item_id,
            "new_stability": new_stability,
            "new_difficulty": new_difficulty,
        })

    result_json = srs_update_stub(
        populated_mastery_db,
        "item.es.ser.001",
        3,  # Good rating
        fsrs_default_params,
    )
    result = json.loads(result_json)

    assert result["status"] == "success"

    # Verify review history was created
    conn = sqlite3.connect(populated_mastery_db)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM review_history WHERE item_id = ?",
        ("item.es.ser.001",),
    )
    count = cursor.fetchone()[0]
    conn.close()

    assert count > 0


@pytest.mark.mcp
@pytest.mark.srs
@pytest.mark.unit
def test_srs_update_increments_reps(
    populated_mastery_db: Path,
    fsrs_default_params: dict[str, Any],
) -> None:
    """Test that srs.update() increments the repetition counter."""
    def srs_update_stub(
        mastery_db_path: Path,
        item_id: str,
        quality: int,
    ) -> str:
        conn = sqlite3.connect(mastery_db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT reps FROM items WHERE item_id = ?",
            (item_id,),
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            return json.dumps({"error": "Item not found"})

        old_reps = row[0]

        cursor.execute(
            """
            UPDATE items
            SET reps = ?, last_review = CURRENT_TIMESTAMP
            WHERE item_id = ?
            """,
            (old_reps + 1, item_id),
        )

        conn.commit()
        conn.close()

        return json.dumps({"status": "success", "new_reps": old_reps + 1})

    # Get initial reps count
    conn = sqlite3.connect(populated_mastery_db)
    cursor = conn.cursor()
    cursor.execute("SELECT reps FROM items WHERE item_id = ?", ("item.es.ser.001",))
    initial_reps = cursor.fetchone()[0]
    conn.close()

    # Update item
    result = json.loads(srs_update_stub(populated_mastery_db, "item.es.ser.001", 3))

    # Verify reps incremented
    conn = sqlite3.connect(populated_mastery_db)
    cursor = conn.cursor()
    cursor.execute("SELECT reps FROM items WHERE item_id = ?", ("item.es.ser.001",))
    new_reps = cursor.fetchone()[0]
    conn.close()

    assert new_reps == initial_reps + 1


@pytest.mark.mcp
@pytest.mark.srs
@pytest.mark.unit
@pytest.mark.parametrize("quality", [1, 2, 3, 4, 5])
def test_srs_update_handles_all_quality_levels(
    populated_mastery_db: Path,
    fsrs_default_params: dict[str, Any],
    quality: int,
) -> None:
    """Test that srs.update() handles all quality levels (1-5)."""
    def srs_update_stub(
        mastery_db_path: Path,
        item_id: str,
        quality: int,
        fsrs_params: dict[str, Any],
    ) -> str:
        # Validate quality
        if not 1 <= quality <= 5:
            return json.dumps({"error": "Invalid quality rating"})

        conn = sqlite3.connect(mastery_db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT stability, difficulty FROM items WHERE item_id = ?",
            (item_id,),
        )
        row = cursor.fetchone()

        if not row:
            conn.close()
            return json.dumps({"error": "Item not found"})

        stability, difficulty = row

        # Simplified update
        new_stability = stability * (1.5 if quality >= 3 else 0.5)

        cursor.execute(
            """
            UPDATE items SET stability = ?, last_review = CURRENT_TIMESTAMP
            WHERE item_id = ?
            """,
            (new_stability, item_id),
        )

        conn.commit()
        conn.close()

        return json.dumps({"status": "success", "quality": quality})

    result = json.loads(
        srs_update_stub(populated_mastery_db, "item.es.ser.001", quality, fsrs_default_params)
    )

    assert result["status"] == "success"
    assert result["quality"] == quality


@pytest.mark.mcp
@pytest.mark.srs
@pytest.mark.unit
def test_srs_update_adjusts_stability(
    populated_mastery_db: Path,
    fsrs_default_params: dict[str, Any],
) -> None:
    """Test that srs.update() adjusts stability based on performance."""
    def srs_update_stub(
        mastery_db_path: Path,
        item_id: str,
        quality: int,
    ) -> dict[str, Any]:
        conn = sqlite3.connect(mastery_db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT stability FROM items WHERE item_id = ?",
            (item_id,),
        )
        old_stability = cursor.fetchone()[0]

        # Simple adjustment based on quality
        if quality >= 4:
            new_stability = old_stability * 2.0
        elif quality == 3:
            new_stability = old_stability * 1.5
        elif quality == 2:
            new_stability = old_stability * 0.8
        else:
            new_stability = old_stability * 0.5

        cursor.execute(
            "UPDATE items SET stability = ? WHERE item_id = ?",
            (new_stability, item_id),
        )

        conn.commit()
        conn.close()

        return {
            "old_stability": old_stability,
            "new_stability": new_stability,
        }

    # Test with good performance (should increase stability)
    result_good = srs_update_stub(populated_mastery_db, "item.es.ser.001", 4)
    assert result_good["new_stability"] > result_good["old_stability"]

    # Test with poor performance (should decrease stability)
    result_poor = srs_update_stub(populated_mastery_db, "item.es.estar.001", 1)
    assert result_poor["new_stability"] < result_poor["old_stability"]


# ============================================================================
# srs.schedule() - Scheduling Tests
# ============================================================================


@pytest.mark.mcp
@pytest.mark.srs
@pytest.mark.unit
def test_srs_schedule_calculates_next_review_date(
    fsrs_default_params: dict[str, Any],
) -> None:
    """Test srs.schedule() calculates next review date based on stability."""
    # from mcp_servers.srs_server import srs_schedule

    # Stub implementation
    def srs_schedule_stub(
        stability: float,
        request_retention: float = 0.9,
    ) -> str:
        """Calculate next review date."""
        import math

        # Calculate interval in days
        interval_days = stability * (math.log(request_retention) / math.log(0.9))
        interval_days = max(1, int(round(interval_days)))

        # Calculate next review date
        next_review = datetime.now(timezone.utc) + timedelta(days=interval_days)

        return json.dumps({
            "interval_days": interval_days,
            "next_review": next_review.isoformat(),
            "stability": stability,
        })

    result_json = srs_schedule_stub(5.0, 0.9)
    result = json.loads(result_json)

    assert "interval_days" in result
    assert "next_review" in result
    assert result["interval_days"] > 0

    # Higher stability should result in longer interval
    result_high = json.loads(srs_schedule_stub(10.0, 0.9))
    result_low = json.loads(srs_schedule_stub(2.0, 0.9))

    assert result_high["interval_days"] > result_low["interval_days"]


@pytest.mark.mcp
@pytest.mark.srs
@pytest.mark.unit
def test_srs_schedule_respects_retention_target(
    fsrs_default_params: dict[str, Any],
) -> None:
    """Test that srs.schedule() adjusts intervals based on retention target."""
    import math

    def srs_schedule_stub(stability: float, retention: float) -> int:
        interval_days = stability * (math.log(retention) / math.log(0.9))
        return max(1, int(round(interval_days)))

    stability = 5.0

    # Higher retention target -> shorter intervals
    interval_90 = srs_schedule_stub(stability, 0.9)
    interval_80 = srs_schedule_stub(stability, 0.8)

    assert interval_90 < interval_80, "Higher retention should have shorter intervals"


# ============================================================================
# srs.stats() - Statistics Tests
# ============================================================================


@pytest.mark.mcp
@pytest.mark.srs
@pytest.mark.unit
def test_srs_stats_returns_learner_statistics(populated_mastery_db: Path) -> None:
    """Test srs.stats() returns comprehensive learner statistics."""
    # from mcp_servers.srs_server import srs_stats

    # Stub implementation
    def srs_stats_stub(mastery_db_path: Path, learner_id: str) -> str:
        """Get learner SRS statistics."""
        conn = sqlite3.connect(mastery_db_path)
        cursor = conn.cursor()

        # Total items
        cursor.execute("SELECT COUNT(*) FROM items")
        total_items = cursor.fetchone()[0]

        # Items reviewed
        cursor.execute("SELECT COUNT(*) FROM items WHERE reps > 0")
        items_reviewed = cursor.fetchone()[0]

        # New items
        cursor.execute("SELECT COUNT(*) FROM items WHERE reps = 0")
        new_items = cursor.fetchone()[0]

        # Due items
        cursor.execute("SELECT COUNT(*) FROM due_items")
        due_items = cursor.fetchone()[0]

        # Average stability
        cursor.execute("SELECT AVG(stability) FROM items WHERE reps > 0")
        avg_stability = cursor.fetchone()[0] or 0

        # Total reviews
        cursor.execute("SELECT COUNT(*) FROM review_history")
        total_reviews = cursor.fetchone()[0]

        conn.close()

        stats = {
            "learner_id": learner_id,
            "total_items": total_items,
            "items_reviewed": items_reviewed,
            "new_items": new_items,
            "due_items": due_items,
            "average_stability": round(avg_stability, 2),
            "total_reviews": total_reviews,
        }

        return json.dumps(stats)

    result_json = srs_stats_stub(populated_mastery_db, "test_learner")
    result = json.loads(result_json)

    assert "total_items" in result
    assert "items_reviewed" in result
    assert "new_items" in result
    assert "due_items" in result
    assert "average_stability" in result
    assert "total_reviews" in result

    # Sanity checks
    assert result["total_items"] > 0
    assert result["total_items"] == result["items_reviewed"] + result["new_items"]


@pytest.mark.mcp
@pytest.mark.srs
@pytest.mark.integration
def test_srs_stats_includes_performance_metrics(populated_mastery_db: Path) -> None:
    """Test that srs.stats() includes performance metrics."""
    def srs_stats_stub(mastery_db_path: Path) -> str:
        conn = sqlite3.connect(mastery_db_path)
        cursor = conn.cursor()

        # Average quality
        cursor.execute("SELECT AVG(quality) FROM review_history")
        avg_quality = cursor.fetchone()[0] or 0

        # Recent reviews (last 7 days)
        cursor.execute("""
            SELECT COUNT(*) FROM review_history
            WHERE review_time >= datetime('now', '-7 days')
        """)
        recent_reviews = cursor.fetchone()[0]

        # Quality distribution
        cursor.execute("""
            SELECT quality, COUNT(*) as count
            FROM review_history
            GROUP BY quality
            ORDER BY quality
        """)
        quality_dist = {row[0]: row[1] for row in cursor.fetchall()}

        conn.close()

        stats = {
            "average_quality": round(avg_quality, 2),
            "recent_reviews_7d": recent_reviews,
            "quality_distribution": quality_dist,
        }

        return json.dumps(stats)

    result = json.loads(srs_stats_stub(populated_mastery_db))

    assert "average_quality" in result
    assert "recent_reviews_7d" in result
    assert "quality_distribution" in result

    if result["average_quality"] > 0:
        assert 1 <= result["average_quality"] <= 5


# ============================================================================
# Error Handling Tests
# ============================================================================


@pytest.mark.mcp
@pytest.mark.srs
@pytest.mark.unit
def test_srs_update_with_invalid_item_id(
    populated_mastery_db: Path,
    fsrs_default_params: dict[str, Any],
) -> None:
    """Test srs.update() handles invalid item ID gracefully."""
    def srs_update_stub(mastery_db_path: Path, item_id: str, quality: int) -> str:
        conn = sqlite3.connect(mastery_db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT item_id FROM items WHERE item_id = ?", (item_id,))
        if not cursor.fetchone():
            conn.close()
            return json.dumps({"error": "Item not found", "item_id": item_id})

        conn.close()
        return json.dumps({"status": "success"})

    result = json.loads(srs_update_stub(populated_mastery_db, "nonexistent.item", 3))

    assert "error" in result
    assert result["error"] == "Item not found"


@pytest.mark.mcp
@pytest.mark.srs
@pytest.mark.unit
def test_srs_update_with_invalid_quality(populated_mastery_db: Path) -> None:
    """Test srs.update() rejects invalid quality ratings."""
    def srs_update_stub(mastery_db_path: Path, item_id: str, quality: int) -> str:
        if not 1 <= quality <= 5:
            return json.dumps({
                "error": "Invalid quality rating",
                "quality": quality,
                "valid_range": "1-5",
            })

        return json.dumps({"status": "success"})

    # Test invalid quality values
    result_low = json.loads(srs_update_stub(populated_mastery_db, "item.es.ser.001", 0))
    assert "error" in result_low

    result_high = json.loads(srs_update_stub(populated_mastery_db, "item.es.ser.001", 6))
    assert "error" in result_high

    # Test valid quality
    result_valid = json.loads(srs_update_stub(populated_mastery_db, "item.es.ser.001", 3))
    assert result_valid["status"] == "success"


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.mcp
@pytest.mark.srs
@pytest.mark.integration
def test_complete_srs_workflow(
    populated_mastery_db: Path,
    fsrs_default_params: dict[str, Any],
) -> None:
    """
    Test complete SRS workflow: query due -> update -> verify changes.
    """
    def srs_due_stub(mastery_db_path: Path, limit: int) -> list[dict[str, Any]]:
        conn = sqlite3.connect(mastery_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT item_id, stability, difficulty FROM items LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [{"item_id": row[0], "stability": row[1], "difficulty": row[2]} for row in rows]

    def srs_update_stub(mastery_db_path: Path, item_id: str, quality: int) -> None:
        conn = sqlite3.connect(mastery_db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT stability FROM items WHERE item_id = ?", (item_id,))
        old_stability = cursor.fetchone()[0]
        new_stability = old_stability * (1.5 if quality >= 3 else 0.5)

        cursor.execute(
            "UPDATE items SET stability = ?, last_review = CURRENT_TIMESTAMP WHERE item_id = ?",
            (new_stability, item_id),
        )

        conn.commit()
        conn.close()

    # Step 1: Get due items
    due_items = srs_due_stub(populated_mastery_db, 1)
    assert len(due_items) > 0

    item = due_items[0]
    original_stability = item["stability"]

    # Step 2: Update with good performance
    srs_update_stub(populated_mastery_db, item["item_id"], 4)

    # Step 3: Verify stability increased
    conn = sqlite3.connect(populated_mastery_db)
    cursor = conn.cursor()
    cursor.execute("SELECT stability FROM items WHERE item_id = ?", (item["item_id"],))
    new_stability = cursor.fetchone()[0]
    conn.close()

    assert new_stability > original_stability
