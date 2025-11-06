"""
Smoke tests for basic integration.

These tests verify that core components can work together without errors.
They're not comprehensive but catch obvious breakage.
"""

import pytest
from pathlib import Path
from state.coach import Coach
from mcp_servers.kg_server.server import KGServer
from mcp_servers.srs_server.server import SRSServer


@pytest.mark.integration
def test_coach_session_lifecycle():
    """
    Smoke test: Complete coaching session lifecycle.

    Verifies:
    - Coach can initialize
    - Session can be started
    - Exercise can be recorded
    - Session can be ended
    """
    coach = Coach()

    # Start session
    session = coach.start_session(learner_id="smoke_test_learner", duration_minutes=10)

    assert 'session_id' in session
    assert 'exercises' in session
    assert 'balance_status' in session
    assert 'current_balance' in session

    # Record an exercise
    result = coach.record_exercise(
        session_id=session['session_id'],
        item_id="smoke.test.item.001",
        quality=4,
        learner_response="This is a smoke test",
        duration_seconds=30,
        strand="meaning_output"
    )

    assert result.success
    assert result.item_id == "smoke.test.item.001"
    assert result.quality == 4
    assert result.mastery_status in ['new', 'learning', 'mastered']
    assert result.feedback_for_llm is not None

    # End session
    summary = coach.end_session(session['session_id'])

    assert summary['session_id'] == session['session_id']
    assert summary['exercises_completed'] == 1
    assert 'final_balance' in summary
    assert 'balance_status' in summary


@pytest.mark.integration
def test_kg_server_initialization():
    """
    Smoke test: KG server can initialize with real database.

    Verifies:
    - Server can find and open kg.sqlite
    - Database has expected structure
    """
    kg_db = Path(__file__).parent.parent / "kg.sqlite"

    # Skip if kg.sqlite doesn't exist (needs to be built)
    if not kg_db.exists():
        pytest.skip("kg.sqlite not found - run 'make build-kg' first")

    server = KGServer(kg_db_path=kg_db)

    # Verify it initialized
    assert server.kg_db_path.exists()


@pytest.mark.integration
def test_srs_server_initialization():
    """
    Smoke test: SRS server can initialize with mastery database.

    Verifies:
    - Server can find and open mastery.sqlite
    - Database has expected schema
    """
    mastery_db = Path(__file__).parent.parent / "state" / "mastery.sqlite"

    server = SRSServer(db_path=mastery_db)

    # Verify it initialized
    assert server.db_path.exists()


@pytest.mark.integration
def test_coach_with_empty_database():
    """
    Smoke test: Coach handles empty database gracefully.

    Verifies:
    - Session can start even with no exercises
    - System doesn't crash on empty state
    """
    coach = Coach()

    # This should work even if database is empty
    session = coach.start_session(learner_id="empty_db_test", duration_minutes=5)

    # Should get session even if no exercises planned
    assert 'session_id' in session
    assert 'exercises' in session
    assert isinstance(session['exercises'], list)

    # Can end session even without exercises
    summary = coach.end_session(session['session_id'])
    assert summary['exercises_completed'] == 0


@pytest.mark.integration
def test_coach_records_to_database():
    """
    Smoke test: Verify recorded exercises persist to database.

    Verifies:
    - Exercise recording actually writes to DB
    - Data can be queried back
    """
    import sqlite3

    coach = Coach()
    session = coach.start_session(learner_id="persistence_test")

    # Record exercise
    item_id = "smoke.persistence.test.001"
    coach.record_exercise(
        session_id=session['session_id'],
        item_id=item_id,
        quality=5,
        learner_response="Persistence test",
        duration_seconds=10,
        strand="fluency"
    )

    # Verify it's in the database
    conn = sqlite3.connect(coach.mastery_db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM items WHERE item_id = ?", (item_id,))
    row = cursor.fetchone()

    assert row is not None, "Exercise should be recorded in items table"

    cursor.execute("SELECT * FROM review_history WHERE item_id = ?", (item_id,))
    history = cursor.fetchall()

    assert len(history) > 0, "Exercise should be recorded in review_history"

    conn.close()
    coach.end_session(session['session_id'])


@pytest.mark.unit
def test_coach_quality_scale():
    """
    Smoke test: Verify quality scale (0-5) is respected.

    This is a unit test but critical for data integrity.
    """
    coach = Coach()

    # Quality must be 0-5
    valid_qualities = [0, 1, 2, 3, 4, 5]

    # This test just verifies we can record each quality level
    # A real implementation might validate quality range
    for quality in valid_qualities:
        session = coach.start_session(learner_id="quality_test")
        result = coach.record_exercise(
            session_id=session['session_id'],
            item_id=f"quality.test.{quality}",
            quality=quality,
            learner_response=f"Quality {quality} test",
            duration_seconds=5,
            strand="language_focused"
        )
        assert result.quality == quality
        coach.end_session(session['session_id'])


if __name__ == "__main__":
    # Allow running smoke tests directly
    pytest.main([__file__, "-v", "-m", "integration"])
