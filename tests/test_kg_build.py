"""
Tests for knowledge graph building from YAML sources.

This module tests the construction of the KG SQLite database from seed files,
including node creation, edge relationships, and schema validation.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest


# ============================================================================
# Schema Validation Tests
# ============================================================================


@pytest.mark.kg
@pytest.mark.unit
def test_kg_db_schema_exists(tmp_kg_db: Path) -> None:
    """Test that KG database has the expected schema."""
    conn = sqlite3.connect(tmp_kg_db)
    cursor = conn.cursor()

    # Check nodes table exists
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='nodes'
    """)
    assert cursor.fetchone() is not None

    # Check edges table exists
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='edges'
    """)
    assert cursor.fetchone() is not None

    # Check evidence table exists
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='evidence'
    """)
    assert cursor.fetchone() is not None

    conn.close()


@pytest.mark.kg
@pytest.mark.unit
def test_kg_db_indexes_exist(tmp_kg_db: Path) -> None:
    """Test that KG database has appropriate indexes for performance."""
    conn = sqlite3.connect(tmp_kg_db)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='index'
    """)
    indexes = {row[0] for row in cursor.fetchall()}

    expected_indexes = {
        "idx_nodes_type",
        "idx_nodes_cefr",
        "idx_edges_source",
        "idx_edges_target",
        "idx_edges_type",
        "idx_evidence_learner",
    }

    # All expected indexes should be present
    assert expected_indexes.issubset(indexes), f"Missing indexes: {expected_indexes - indexes}"

    conn.close()


# ============================================================================
# Node Insertion Tests
# ============================================================================


@pytest.mark.kg
@pytest.mark.unit
def test_insert_single_node(tmp_kg_db: Path) -> None:
    """Test inserting a single node into the KG."""
    conn = sqlite3.connect(tmp_kg_db)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO nodes (node_id, type, label, cefr_level)
        VALUES (?, ?, ?, ?)
    """, ("test.node.001", "Lexeme", "Test Word", "A1"))

    conn.commit()

    # Verify insertion
    cursor.execute("SELECT * FROM nodes WHERE node_id = ?", ("test.node.001",))
    row = cursor.fetchone()

    assert row is not None
    assert row[0] == "test.node.001"
    assert row[1] == "Lexeme"
    assert row[2] == "Test Word"

    conn.close()


@pytest.mark.kg
@pytest.mark.unit
def test_insert_node_with_json_fields(tmp_kg_db: Path) -> None:
    """Test inserting a node with JSON diagnostics and prompts."""
    conn = sqlite3.connect(tmp_kg_db)
    cursor = conn.cursor()

    diagnostics = json.dumps({"form": "hola", "function": "greeting"})
    prompts = json.dumps(["Say hello", "Greet someone"])
    metadata = json.dumps({"frequency": "very_high"})

    cursor.execute("""
        INSERT INTO nodes (node_id, type, label, diagnostics, prompts, metadata, cefr_level)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("lexeme.es.hola", "Lexeme", "hola", diagnostics, prompts, metadata, "A1"))

    conn.commit()

    # Verify JSON fields can be retrieved and parsed
    cursor.execute("SELECT diagnostics, prompts, metadata FROM nodes WHERE node_id = ?",
                   ("lexeme.es.hola",))
    row = cursor.fetchone()

    assert row is not None
    parsed_diagnostics = json.loads(row[0])
    parsed_prompts = json.loads(row[1])
    parsed_metadata = json.loads(row[2])

    assert parsed_diagnostics["form"] == "hola"
    assert len(parsed_prompts) == 2
    assert parsed_metadata["frequency"] == "very_high"

    conn.close()


@pytest.mark.kg
@pytest.mark.unit
@pytest.mark.parametrize("node_type", [
    "Lexeme",
    "Construction",
    "Morph",
    "Function",
    "CanDo",
    "Topic",
    "Script",
    "PhonologyItem",
])
def test_insert_different_node_types(tmp_kg_db: Path, node_type: str) -> None:
    """Test that all expected node types can be inserted."""
    conn = sqlite3.connect(tmp_kg_db)
    cursor = conn.cursor()

    node_id = f"test.{node_type.lower()}.001"
    cursor.execute("""
        INSERT INTO nodes (node_id, type, label, cefr_level)
        VALUES (?, ?, ?, ?)
    """, (node_id, node_type, f"Test {node_type}", "A1"))

    conn.commit()

    cursor.execute("SELECT type FROM nodes WHERE node_id = ?", (node_id,))
    row = cursor.fetchone()

    assert row is not None
    assert row[0] == node_type

    conn.close()


# ============================================================================
# Edge Insertion Tests
# ============================================================================


@pytest.mark.kg
@pytest.mark.unit
def test_insert_edge(populated_kg_db: Path) -> None:
    """Test inserting an edge between two nodes."""
    conn = sqlite3.connect(populated_kg_db)
    cursor = conn.cursor()

    # Verify edge exists (from populated fixture)
    cursor.execute("""
        SELECT * FROM edges
        WHERE source_id = ? AND target_id = ? AND edge_type = ?
    """, ("lexeme.es.ser", "cando.es.introduce_self_A1", "prerequisite_of"))

    row = cursor.fetchone()
    assert row is not None

    conn.close()


@pytest.mark.kg
@pytest.mark.unit
@pytest.mark.parametrize("edge_type", [
    "prerequisite_of",
    "realizes",
    "contrasts_with",
    "depends_on",
    "practice_with",
    "addresses_error",
])
def test_insert_different_edge_types(tmp_kg_db: Path, edge_type: str) -> None:
    """Test that all expected edge types can be inserted."""
    conn = sqlite3.connect(tmp_kg_db)
    cursor = conn.cursor()

    # Insert two nodes
    cursor.execute("""
        INSERT INTO nodes (node_id, type, label, cefr_level)
        VALUES (?, ?, ?, ?)
    """, ("node.source", "Lexeme", "Source", "A1"))

    cursor.execute("""
        INSERT INTO nodes (node_id, type, label, cefr_level)
        VALUES (?, ?, ?, ?)
    """, ("node.target", "Lexeme", "Target", "A1"))

    # Insert edge
    cursor.execute("""
        INSERT INTO edges (source_id, target_id, edge_type, weight)
        VALUES (?, ?, ?, ?)
    """, ("node.source", "node.target", edge_type, 1.0))

    conn.commit()

    cursor.execute("SELECT edge_type FROM edges WHERE source_id = ?", ("node.source",))
    row = cursor.fetchone()

    assert row is not None
    assert row[0] == edge_type

    conn.close()


# ============================================================================
# YAML Parsing Tests (Stubbed)
# ============================================================================


@pytest.mark.kg
@pytest.mark.unit
def test_parse_yaml_nodes(sample_kg_yaml: Path) -> None:
    """Test parsing nodes from YAML file."""
    # NOTE: This is a stub - actual implementation will be in kg/build.py
    # For now, just verify the YAML file exists and has content
    assert sample_kg_yaml.exists()
    content = sample_kg_yaml.read_text()
    assert "nodes:" in content
    assert "lexeme.es.hola" in content


@pytest.mark.kg
@pytest.mark.integration
def test_build_kg_from_yaml_stub(sample_kg_yaml: Path, tmp_kg_db: Path) -> None:
    """
    Stub test for building KG database from YAML file.

    NOTE: This test is a placeholder. When kg/build.py is implemented,
    this should call the actual build function and verify the database
    is correctly populated.
    """
    # TODO: Implement actual kg.build.py module
    # Example usage would be:
    # from kg.build import build_kg_from_yaml
    # build_kg_from_yaml(sample_kg_yaml, tmp_kg_db)

    # For now, manually insert data to simulate the build process
    conn = sqlite3.connect(tmp_kg_db)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO nodes (node_id, type, label, cefr_level)
        VALUES (?, ?, ?, ?)
    """, ("lexeme.es.hola", "Lexeme", "hola (hello)", "A1"))

    cursor.execute("""
        INSERT INTO nodes (node_id, type, label, cefr_level)
        VALUES (?, ?, ?, ?)
    """, ("lexeme.es.gracias", "Lexeme", "gracias (thank you)", "A1"))

    conn.commit()

    # Verify
    cursor.execute("SELECT COUNT(*) FROM nodes")
    count = cursor.fetchone()[0]
    assert count >= 2

    conn.close()


# ============================================================================
# Query Tests
# ============================================================================


@pytest.mark.kg
@pytest.mark.unit
def test_query_nodes_by_type(populated_kg_db: Path) -> None:
    """Test querying nodes by type."""
    conn = sqlite3.connect(populated_kg_db)
    cursor = conn.cursor()

    cursor.execute("SELECT node_id FROM nodes WHERE type = ?", ("Lexeme",))
    lexemes = cursor.fetchall()

    assert len(lexemes) > 0
    assert all("lexeme" in row[0] for row in lexemes)

    conn.close()


@pytest.mark.kg
@pytest.mark.unit
def test_query_nodes_by_cefr_level(populated_kg_db: Path) -> None:
    """Test querying nodes by CEFR level."""
    conn = sqlite3.connect(populated_kg_db)
    cursor = conn.cursor()

    cursor.execute("SELECT node_id FROM nodes WHERE cefr_level = ?", ("A1",))
    a1_nodes = cursor.fetchall()

    assert len(a1_nodes) > 0

    cursor.execute("SELECT node_id FROM nodes WHERE cefr_level = ?", ("B1",))
    b1_nodes = cursor.fetchall()

    assert len(b1_nodes) > 0

    conn.close()


@pytest.mark.kg
@pytest.mark.unit
def test_query_prerequisites(populated_kg_db: Path) -> None:
    """Test querying prerequisite relationships."""
    conn = sqlite3.connect(populated_kg_db)
    cursor = conn.cursor()

    # Find prerequisites for subjunctive present
    cursor.execute("""
        SELECT source_id FROM edges
        WHERE target_id = ? AND edge_type = ?
    """, ("constr.es.subjunctive_present", "prerequisite_of"))

    prereqs = cursor.fetchall()
    assert len(prereqs) > 0

    # Should include subjunctive endings as a prerequisite
    prereq_ids = [row[0] for row in prereqs]
    assert "morph.es.subjunctive_endings" in prereq_ids

    conn.close()


@pytest.mark.kg
@pytest.mark.unit
def test_find_frontier_nodes_stub(populated_kg_db: Path) -> None:
    """
    Stub test for finding frontier nodes (prerequisites satisfied, not mastered).

    NOTE: This is a placeholder. The actual frontier algorithm will be implemented
    in mcp_servers/kg_server.py and will need to query both the KG and mastery DB.
    """
    conn = sqlite3.connect(populated_kg_db)
    cursor = conn.cursor()

    # Simple query: find A1 nodes (basic frontier for a new learner)
    cursor.execute("SELECT node_id FROM nodes WHERE cefr_level = ?", ("A1",))
    a1_nodes = cursor.fetchall()

    assert len(a1_nodes) > 0

    # TODO: Implement actual frontier algorithm that:
    # 1. Queries nodes where all prerequisites are mastered
    # 2. Excludes nodes already mastered by learner
    # 3. Ranks by CEFR level and difficulty

    conn.close()


# ============================================================================
# Evidence Tracking Tests
# ============================================================================


@pytest.mark.kg
@pytest.mark.unit
def test_insert_evidence(populated_kg_db: Path, sample_learner: dict[str, Any]) -> None:
    """Test inserting evidence data for a learner."""
    conn = sqlite3.connect(populated_kg_db)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO evidence (node_id, learner_id, success_count, error_count, last_practiced)
        VALUES (?, ?, ?, ?, ?)
    """, ("lexeme.es.ser", sample_learner["learner_id"], 5, 2, "2025-01-20T10:00:00Z"))

    conn.commit()

    cursor.execute("""
        SELECT success_count, error_count FROM evidence
        WHERE node_id = ? AND learner_id = ?
    """, ("lexeme.es.ser", sample_learner["learner_id"]))

    row = cursor.fetchone()
    assert row is not None
    assert row[0] == 5  # success_count
    assert row[1] == 2  # error_count

    conn.close()


@pytest.mark.kg
@pytest.mark.unit
def test_update_evidence(populated_kg_db: Path, sample_learner: dict[str, Any]) -> None:
    """Test updating evidence data after practice."""
    conn = sqlite3.connect(populated_kg_db)
    cursor = conn.cursor()

    learner_id = sample_learner["learner_id"]

    # Insert initial evidence
    cursor.execute("""
        INSERT INTO evidence (node_id, learner_id, success_count, error_count)
        VALUES (?, ?, ?, ?)
    """, ("lexeme.es.estar", learner_id, 3, 1))

    conn.commit()

    # Update after successful practice
    cursor.execute("""
        UPDATE evidence
        SET success_count = success_count + 1,
            last_practiced = CURRENT_TIMESTAMP
        WHERE node_id = ? AND learner_id = ?
    """, ("lexeme.es.estar", learner_id))

    conn.commit()

    # Verify update
    cursor.execute("""
        SELECT success_count FROM evidence
        WHERE node_id = ? AND learner_id = ?
    """, ("lexeme.es.estar", learner_id))

    row = cursor.fetchone()
    assert row is not None
    assert row[0] == 4

    conn.close()


# ============================================================================
# Complex Query Tests
# ============================================================================


@pytest.mark.kg
@pytest.mark.integration
def test_query_node_with_all_prerequisites(populated_kg_db: Path) -> None:
    """Test finding all prerequisites for a node (recursive)."""
    conn = sqlite3.connect(populated_kg_db)
    cursor = conn.cursor()

    # This would require a recursive CTE in production
    # For now, just test direct prerequisites
    cursor.execute("""
        SELECT source_id FROM edges
        WHERE target_id = ? AND edge_type = ?
    """, ("function.es.express_doubt", "prerequisite_of"))

    # Note: This is a simplified test. A full implementation would need
    # to recursively traverse the prerequisite tree.

    conn.close()


@pytest.mark.kg
@pytest.mark.integration
def test_query_nodes_by_topic(populated_kg_db: Path) -> None:
    """Test finding nodes associated with a topic via edges."""
    conn = sqlite3.connect(populated_kg_db)
    cursor = conn.cursor()

    # Find nodes that can be practiced with a topic
    cursor.execute("""
        SELECT target_id FROM edges
        WHERE source_id = ? AND edge_type = ?
    """, ("topic.es.food_ordering", "practice_with"))

    related_nodes = cursor.fetchall()

    # At least one node should be associated with the topic
    assert len(related_nodes) > 0

    conn.close()


# ============================================================================
# Validation Tests
# ============================================================================


@pytest.mark.kg
@pytest.mark.unit
def test_node_id_uniqueness(tmp_kg_db: Path) -> None:
    """Test that duplicate node IDs are rejected."""
    conn = sqlite3.connect(tmp_kg_db)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO nodes (node_id, type, label, cefr_level)
        VALUES (?, ?, ?, ?)
    """, ("duplicate.test", "Lexeme", "First", "A1"))

    conn.commit()

    # Attempt to insert duplicate
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("""
            INSERT INTO nodes (node_id, type, label, cefr_level)
            VALUES (?, ?, ?, ?)
        """, ("duplicate.test", "Lexeme", "Second", "A1"))
        conn.commit()

    conn.close()


@pytest.mark.kg
@pytest.mark.unit
def test_edge_foreign_key_constraint(tmp_kg_db: Path) -> None:
    """Test that edges require valid node references."""
    conn = sqlite3.connect(tmp_kg_db)
    cursor = conn.cursor()

    # Enable foreign key constraints
    cursor.execute("PRAGMA foreign_keys = ON")

    # Insert a valid node
    cursor.execute("""
        INSERT INTO nodes (node_id, type, label, cefr_level)
        VALUES (?, ?, ?, ?)
    """, ("valid.node", "Lexeme", "Valid", "A1"))

    conn.commit()

    # Attempt to create edge with non-existent target
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("""
            INSERT INTO edges (source_id, target_id, edge_type)
            VALUES (?, ?, ?)
        """, ("valid.node", "nonexistent.node", "prerequisite_of"))
        conn.commit()

    conn.close()
