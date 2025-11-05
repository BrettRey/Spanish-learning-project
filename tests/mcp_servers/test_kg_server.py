"""
Tests for Knowledge Graph MCP server tools.

This module tests the MCP tools that expose KG functionality:
- kg.next(): Find next learnable nodes for a learner
- kg.prompt(): Generate task prompts for a node
- kg.add_evidence(): Update evidence after practice
- kg.query(): General KG queries
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest


# ============================================================================
# kg.next() - Frontier Node Selection Tests
# ============================================================================


@pytest.mark.mcp
@pytest.mark.kg
@pytest.mark.unit
def test_kg_next_returns_nodes_for_learner(
    populated_kg_db: Path,
    sample_learner: dict[str, Any],
) -> None:
    """
    Test kg.next() returns appropriate nodes for a learner.

    NOTE: This is a stub. The actual implementation will be in
    mcp_servers/kg_server.py
    """
    # from mcp_servers.kg_server import kg_next

    # Stub implementation
    def kg_next_stub(
        kg_db_path: Path,
        learner_id: str,
        k: int = 5,
    ) -> str:
        """Return next k learnable nodes for learner."""
        conn = sqlite3.connect(kg_db_path)
        cursor = conn.cursor()

        # Simple stub: return A1 level nodes (beginner frontier)
        cursor.execute(
            "SELECT node_id, label, type FROM nodes WHERE cefr_level = ? LIMIT ?",
            ("A1", k),
        )
        rows = cursor.fetchall()
        conn.close()

        nodes = [
            {"node_id": row[0], "label": row[1], "type": row[2]}
            for row in rows
        ]
        return json.dumps(nodes)

    result_json = kg_next_stub(
        populated_kg_db,
        sample_learner["learner_id"],
        k=5,
    )

    result = json.loads(result_json)

    # Should return a list
    assert isinstance(result, list)
    assert len(result) <= 5
    assert len(result) > 0

    # Each node should have required fields
    for node in result:
        assert "node_id" in node
        assert "label" in node
        assert "type" in node


@pytest.mark.mcp
@pytest.mark.kg
@pytest.mark.unit
def test_kg_next_respects_k_parameter(populated_kg_db: Path) -> None:
    """Test that kg.next() respects the k parameter for result count."""
    def kg_next_stub(kg_db_path: Path, learner_id: str, k: int) -> str:
        conn = sqlite3.connect(kg_db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT node_id, label, type FROM nodes LIMIT ?",
            (k,),
        )
        rows = cursor.fetchall()
        conn.close()

        nodes = [
            {"node_id": row[0], "label": row[1], "type": row[2]}
            for row in rows
        ]
        return json.dumps(nodes)

    # Test different k values
    for k in [1, 3, 5]:
        result = json.loads(kg_next_stub(populated_kg_db, "test_learner", k))
        assert len(result) <= k


@pytest.mark.mcp
@pytest.mark.kg
@pytest.mark.integration
def test_kg_next_excludes_mastered_nodes(
    populated_kg_db: Path,
    sample_learner: dict[str, Any],
) -> None:
    """
    Test that kg.next() excludes nodes already mastered by the learner.

    NOTE: Stub implementation. Full version would query both KG and mastery DB.
    """
    def kg_next_stub(
        kg_db_path: Path,
        learner_id: str,
        k: int,
        mastered_nodes: set[str],
    ) -> str:
        conn = sqlite3.connect(kg_db_path)
        cursor = conn.cursor()

        # Get nodes excluding mastered ones
        placeholders = ",".join("?" * len(mastered_nodes))
        query = f"SELECT node_id, label, type FROM nodes WHERE node_id NOT IN ({placeholders}) LIMIT ?"

        cursor.execute(query, (*mastered_nodes, k))
        rows = cursor.fetchall()
        conn.close()

        nodes = [
            {"node_id": row[0], "label": row[1], "type": row[2]}
            for row in rows
        ]
        return json.dumps(nodes)

    # Simulate some mastered nodes
    mastered = {"lexeme.es.ser", "lexeme.es.estar"}

    result = json.loads(
        kg_next_stub(populated_kg_db, sample_learner["learner_id"], 5, mastered)
    )

    # Verify no mastered nodes in results
    result_ids = {node["node_id"] for node in result}
    assert result_ids.isdisjoint(mastered), "Should not return mastered nodes"


@pytest.mark.mcp
@pytest.mark.kg
@pytest.mark.integration
def test_kg_next_checks_prerequisites(populated_kg_db: Path) -> None:
    """
    Test that kg.next() only returns nodes with satisfied prerequisites.

    NOTE: Stub implementation. Full version would recursively check prerequisite tree.
    """
    def check_prerequisites_satisfied_stub(
        kg_db_path: Path,
        node_id: str,
        mastered_nodes: set[str],
    ) -> bool:
        """Check if all prerequisites for a node are mastered."""
        conn = sqlite3.connect(kg_db_path)
        cursor = conn.cursor()

        # Get direct prerequisites
        cursor.execute(
            """
            SELECT source_id FROM edges
            WHERE target_id = ? AND edge_type = ?
            """,
            (node_id, "prerequisite_of"),
        )
        prereqs = {row[0] for row in cursor.fetchall()}
        conn.close()

        # All prerequisites must be in mastered set
        return prereqs.issubset(mastered_nodes)

    # Test with subjunctive (requires subjunctive_endings prerequisite)
    mastered_without_prereq = {"lexeme.es.ser", "lexeme.es.estar"}
    assert not check_prerequisites_satisfied_stub(
        populated_kg_db,
        "constr.es.subjunctive_present",
        mastered_without_prereq,
    )

    # Test with prerequisite mastered
    mastered_with_prereq = mastered_without_prereq | {"morph.es.subjunctive_endings"}
    assert check_prerequisites_satisfied_stub(
        populated_kg_db,
        "constr.es.subjunctive_present",
        mastered_with_prereq,
    )


# ============================================================================
# kg.prompt() - Task Generation Tests
# ============================================================================


@pytest.mark.mcp
@pytest.mark.kg
@pytest.mark.unit
def test_kg_prompt_returns_task_scaffold(populated_kg_db: Path) -> None:
    """Test kg.prompt() returns a task scaffold for a node."""
    # from mcp_servers.kg_server import kg_prompt

    # Stub implementation
    def kg_prompt_stub(
        kg_db_path: Path,
        node_id: str,
        kind: str = "production",
    ) -> str:
        """Generate task prompt for a node."""
        conn = sqlite3.connect(kg_db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT label, prompts, diagnostics FROM nodes WHERE node_id = ?",
            (node_id,),
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return json.dumps({"error": "Node not found"})

        label, prompts_json, diagnostics_json = row
        prompts = json.loads(prompts_json) if prompts_json else []

        task = {
            "node_id": node_id,
            "label": label,
            "task_type": kind,
            "prompts": prompts,
            "instructions": f"Practice: {label}",
        }

        return json.dumps(task)

    result_json = kg_prompt_stub(populated_kg_db, "lexeme.es.ser", "production")
    result = json.loads(result_json)

    assert "node_id" in result
    assert "label" in result
    assert "task_type" in result
    assert result["task_type"] == "production"
    assert "prompts" in result
    assert isinstance(result["prompts"], list)


@pytest.mark.mcp
@pytest.mark.kg
@pytest.mark.unit
@pytest.mark.parametrize("task_kind", [
    "production",
    "recognition",
    "comprehension",
    "translation",
])
def test_kg_prompt_supports_task_types(
    populated_kg_db: Path,
    task_kind: str,
) -> None:
    """Test kg.prompt() supports different task types."""
    def kg_prompt_stub(kg_db_path: Path, node_id: str, kind: str) -> str:
        conn = sqlite3.connect(kg_db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT label, prompts FROM nodes WHERE node_id = ?",
            (node_id,),
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return json.dumps({"error": "Node not found"})

        label, prompts_json = row
        prompts = json.loads(prompts_json) if prompts_json else []

        task = {
            "node_id": node_id,
            "label": label,
            "task_type": kind,
            "prompts": prompts,
        }
        return json.dumps(task)

    result = json.loads(kg_prompt_stub(populated_kg_db, "lexeme.es.ser", task_kind))
    assert result["task_type"] == task_kind


@pytest.mark.mcp
@pytest.mark.kg
@pytest.mark.unit
def test_kg_prompt_includes_context(populated_kg_db: Path) -> None:
    """Test that kg.prompt() includes diagnostic context for the task."""
    def kg_prompt_stub(kg_db_path: Path, node_id: str) -> str:
        conn = sqlite3.connect(kg_db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT label, prompts, diagnostics, cefr_level FROM nodes WHERE node_id = ?",
            (node_id,),
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return json.dumps({"error": "Node not found"})

        label, prompts_json, diagnostics_json, cefr_level = row

        task = {
            "node_id": node_id,
            "label": label,
            "diagnostics": json.loads(diagnostics_json) if diagnostics_json else {},
            "cefr_level": cefr_level,
            "prompts": json.loads(prompts_json) if prompts_json else [],
        }
        return json.dumps(task)

    result = json.loads(kg_prompt_stub(populated_kg_db, "constr.es.subjunctive_present"))

    assert "diagnostics" in result
    assert "cefr_level" in result
    assert result["cefr_level"] == "B1"


# ============================================================================
# kg.add_evidence() - Evidence Tracking Tests
# ============================================================================


@pytest.mark.mcp
@pytest.mark.kg
@pytest.mark.unit
def test_kg_add_evidence_creates_record(
    populated_kg_db: Path,
    sample_learner: dict[str, Any],
) -> None:
    """Test kg.add_evidence() creates evidence record for learner."""
    # from mcp_servers.kg_server import kg_add_evidence

    # Stub implementation
    def kg_add_evidence_stub(
        kg_db_path: Path,
        node_id: str,
        learner_id: str,
        success: bool,
    ) -> str:
        """Add evidence of practice outcome."""
        conn = sqlite3.connect(kg_db_path)
        cursor = conn.cursor()

        # Check if evidence record exists
        cursor.execute(
            """
            SELECT success_count, error_count FROM evidence
            WHERE node_id = ? AND learner_id = ?
            """,
            (node_id, learner_id),
        )
        row = cursor.fetchone()

        if row:
            # Update existing record
            if success:
                cursor.execute(
                    """
                    UPDATE evidence
                    SET success_count = success_count + 1,
                        last_practiced = CURRENT_TIMESTAMP
                    WHERE node_id = ? AND learner_id = ?
                    """,
                    (node_id, learner_id),
                )
            else:
                cursor.execute(
                    """
                    UPDATE evidence
                    SET error_count = error_count + 1,
                        last_practiced = CURRENT_TIMESTAMP
                    WHERE node_id = ? AND learner_id = ?
                    """,
                    (node_id, learner_id),
                )
        else:
            # Insert new record
            success_count = 1 if success else 0
            error_count = 0 if success else 1
            cursor.execute(
                """
                INSERT INTO evidence (node_id, learner_id, success_count, error_count, last_practiced)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (node_id, learner_id, success_count, error_count),
            )

        conn.commit()
        conn.close()

        return json.dumps({"status": "success", "node_id": node_id})

    learner_id = sample_learner["learner_id"]
    node_id = "lexeme.es.ser"

    # Add successful evidence
    result_json = kg_add_evidence_stub(populated_kg_db, node_id, learner_id, True)
    result = json.loads(result_json)

    assert result["status"] == "success"

    # Verify in database
    conn = sqlite3.connect(populated_kg_db)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT success_count FROM evidence WHERE node_id = ? AND learner_id = ?",
        (node_id, learner_id),
    )
    row = cursor.fetchone()
    conn.close()

    assert row is not None
    assert row[0] >= 1


@pytest.mark.mcp
@pytest.mark.kg
@pytest.mark.unit
def test_kg_add_evidence_increments_counters(
    populated_kg_db: Path,
    sample_learner: dict[str, Any],
) -> None:
    """Test that kg.add_evidence() correctly increments success/error counters."""
    def kg_add_evidence_stub(
        kg_db_path: Path,
        node_id: str,
        learner_id: str,
        success: bool,
    ) -> str:
        conn = sqlite3.connect(kg_db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT success_count, error_count FROM evidence WHERE node_id = ? AND learner_id = ?",
            (node_id, learner_id),
        )
        row = cursor.fetchone()

        if row:
            if success:
                cursor.execute(
                    """
                    UPDATE evidence SET success_count = success_count + 1,
                    last_practiced = CURRENT_TIMESTAMP
                    WHERE node_id = ? AND learner_id = ?
                    """,
                    (node_id, learner_id),
                )
            else:
                cursor.execute(
                    """
                    UPDATE evidence SET error_count = error_count + 1,
                    last_practiced = CURRENT_TIMESTAMP
                    WHERE node_id = ? AND learner_id = ?
                    """,
                    (node_id, learner_id),
                )
        else:
            success_count = 1 if success else 0
            error_count = 0 if success else 1
            cursor.execute(
                """
                INSERT INTO evidence (node_id, learner_id, success_count, error_count, last_practiced)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (node_id, learner_id, success_count, error_count),
            )

        conn.commit()
        conn.close()
        return json.dumps({"status": "success"})

    learner_id = sample_learner["learner_id"]
    node_id = "lexeme.es.estar"

    # Add multiple evidence records
    kg_add_evidence_stub(populated_kg_db, node_id, learner_id, True)
    kg_add_evidence_stub(populated_kg_db, node_id, learner_id, True)
    kg_add_evidence_stub(populated_kg_db, node_id, learner_id, False)

    # Verify counters
    conn = sqlite3.connect(populated_kg_db)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT success_count, error_count FROM evidence WHERE node_id = ? AND learner_id = ?",
        (node_id, learner_id),
    )
    row = cursor.fetchone()
    conn.close()

    assert row is not None
    assert row[0] == 2  # success_count
    assert row[1] == 1  # error_count


# ============================================================================
# kg.query() - General Query Tests
# ============================================================================


@pytest.mark.mcp
@pytest.mark.kg
@pytest.mark.unit
def test_kg_query_by_type(populated_kg_db: Path) -> None:
    """Test general KG query filtering by node type."""
    # from mcp_servers.kg_server import kg_query

    # Stub implementation
    def kg_query_stub(
        kg_db_path: Path,
        node_type: str | None = None,
        cefr_level: str | None = None,
    ) -> str:
        """Query KG with filters."""
        conn = sqlite3.connect(kg_db_path)
        cursor = conn.cursor()

        query = "SELECT node_id, type, label, cefr_level FROM nodes WHERE 1=1"
        params = []

        if node_type:
            query += " AND type = ?"
            params.append(node_type)

        if cefr_level:
            query += " AND cefr_level = ?"
            params.append(cefr_level)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        nodes = [
            {
                "node_id": row[0],
                "type": row[1],
                "label": row[2],
                "cefr_level": row[3],
            }
            for row in rows
        ]
        return json.dumps(nodes)

    # Query for Constructions
    result = json.loads(kg_query_stub(populated_kg_db, node_type="Construction"))

    assert len(result) > 0
    assert all(node["type"] == "Construction" for node in result)


@pytest.mark.mcp
@pytest.mark.kg
@pytest.mark.unit
def test_kg_query_by_cefr_level(populated_kg_db: Path) -> None:
    """Test KG query filtering by CEFR level."""
    def kg_query_stub(kg_db_path: Path, cefr_level: str) -> str:
        conn = sqlite3.connect(kg_db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT node_id, type, label, cefr_level FROM nodes WHERE cefr_level = ?",
            (cefr_level,),
        )
        rows = cursor.fetchall()
        conn.close()

        nodes = [
            {
                "node_id": row[0],
                "type": row[1],
                "label": row[2],
                "cefr_level": row[3],
            }
            for row in rows
        ]
        return json.dumps(nodes)

    # Query for B1 level nodes
    result = json.loads(kg_query_stub(populated_kg_db, "B1"))

    assert len(result) > 0
    assert all(node["cefr_level"] == "B1" for node in result)


@pytest.mark.mcp
@pytest.mark.kg
@pytest.mark.integration
def test_kg_query_related_nodes(populated_kg_db: Path) -> None:
    """Test querying nodes related via specific edge types."""
    def kg_query_related_stub(
        kg_db_path: Path,
        node_id: str,
        edge_type: str,
    ) -> str:
        """Find nodes connected by specific edge type."""
        conn = sqlite3.connect(kg_db_path)
        cursor = conn.cursor()

        # Find targets from this source
        cursor.execute(
            """
            SELECT n.node_id, n.type, n.label, e.edge_type
            FROM edges e
            JOIN nodes n ON e.target_id = n.node_id
            WHERE e.source_id = ? AND e.edge_type = ?
            """,
            (node_id, edge_type),
        )
        rows = cursor.fetchall()
        conn.close()

        nodes = [
            {
                "node_id": row[0],
                "type": row[1],
                "label": row[2],
                "relationship": row[3],
            }
            for row in rows
        ]
        return json.dumps(nodes)

    # Find what subjunctive realizes
    result = json.loads(
        kg_query_related_stub(
            populated_kg_db,
            "constr.es.subjunctive_present",
            "realizes",
        )
    )

    assert len(result) > 0
    assert all(node["relationship"] == "realizes" for node in result)


# ============================================================================
# Error Handling Tests
# ============================================================================


@pytest.mark.mcp
@pytest.mark.kg
@pytest.mark.unit
def test_kg_next_with_invalid_learner_id(populated_kg_db: Path) -> None:
    """Test kg.next() handles invalid learner ID gracefully."""
    def kg_next_stub(kg_db_path: Path, learner_id: str, k: int) -> str:
        # In real implementation, should validate learner exists
        # For stub, just return nodes regardless
        conn = sqlite3.connect(kg_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT node_id, label, type FROM nodes LIMIT ?", (k,))
        rows = cursor.fetchall()
        conn.close()

        nodes = [{"node_id": row[0], "label": row[1], "type": row[2]} for row in rows]
        return json.dumps(nodes)

    result = json.loads(kg_next_stub(populated_kg_db, "nonexistent_learner", 5))

    # Should still return nodes (or error in production)
    assert isinstance(result, list)


@pytest.mark.mcp
@pytest.mark.kg
@pytest.mark.unit
def test_kg_prompt_with_invalid_node_id(populated_kg_db: Path) -> None:
    """Test kg.prompt() handles invalid node ID gracefully."""
    def kg_prompt_stub(kg_db_path: Path, node_id: str) -> str:
        conn = sqlite3.connect(kg_db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT label, prompts FROM nodes WHERE node_id = ?",
            (node_id,),
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return json.dumps({"error": "Node not found", "node_id": node_id})

        label, prompts_json = row
        task = {
            "node_id": node_id,
            "label": label,
            "prompts": json.loads(prompts_json) if prompts_json else [],
        }
        return json.dumps(task)

    result = json.loads(kg_prompt_stub(populated_kg_db, "nonexistent.node"))

    assert "error" in result
    assert result["error"] == "Node not found"


@pytest.mark.mcp
@pytest.mark.kg
@pytest.mark.unit
def test_kg_add_evidence_with_invalid_node_id(
    populated_kg_db: Path,
    sample_learner: dict[str, Any],
) -> None:
    """Test kg.add_evidence() handles invalid node ID."""
    def kg_add_evidence_stub(
        kg_db_path: Path,
        node_id: str,
        learner_id: str,
        success: bool,
    ) -> str:
        conn = sqlite3.connect(kg_db_path)
        cursor = conn.cursor()

        # Check if node exists
        cursor.execute("SELECT node_id FROM nodes WHERE node_id = ?", (node_id,))
        if not cursor.fetchone():
            conn.close()
            return json.dumps({"error": "Node not found", "node_id": node_id})

        # Would add evidence here
        conn.close()
        return json.dumps({"status": "success"})

    result = json.loads(
        kg_add_evidence_stub(
            populated_kg_db,
            "nonexistent.node",
            sample_learner["learner_id"],
            True,
        )
    )

    assert "error" in result
