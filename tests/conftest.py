"""
Shared pytest fixtures for Spanish learning coach tests.

This module provides reusable test fixtures for:
- Temporary databases (KG and mastery)
- Sample learner configurations
- Example knowledge graph nodes
- Mock MCP server contexts
"""

from __future__ import annotations

import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest


# ============================================================================
# Database Fixtures
# ============================================================================


@pytest.fixture
def tmp_kg_db(tmp_path: Path) -> Path:
    """
    Create a temporary knowledge graph SQLite database.

    Args:
        tmp_path: Pytest's temporary directory fixture

    Returns:
        Path to the temporary KG database file

    Example:
        def test_kg_query(tmp_kg_db):
            conn = sqlite3.connect(tmp_kg_db)
            cursor = conn.execute("SELECT * FROM nodes")
            assert cursor is not None
    """
    db_path = tmp_path / "kg_test.sqlite"

    # Create KG schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Nodes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nodes (
            node_id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            label TEXT NOT NULL,
            diagnostics TEXT,
            prompts TEXT,
            cefr_level TEXT,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Edges table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS edges (
            edge_id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id TEXT NOT NULL,
            target_id TEXT NOT NULL,
            edge_type TEXT NOT NULL,
            weight REAL DEFAULT 1.0,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (source_id) REFERENCES nodes(node_id) ON DELETE CASCADE,
            FOREIGN KEY (target_id) REFERENCES nodes(node_id) ON DELETE CASCADE
        )
    """)

    # Evidence table (tracks learner performance on nodes)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evidence (
            evidence_id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT NOT NULL,
            learner_id TEXT NOT NULL,
            success_count INTEGER DEFAULT 0,
            error_count INTEGER DEFAULT 0,
            last_practiced TIMESTAMP,
            FOREIGN KEY (node_id) REFERENCES nodes(node_id) ON DELETE CASCADE,
            UNIQUE(node_id, learner_id)
        )
    """)

    # Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_nodes_cefr ON nodes(cefr_level)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id)"
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_type ON edges(edge_type)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_evidence_learner ON evidence(learner_id)"
    )

    conn.commit()
    conn.close()

    return db_path


@pytest.fixture
def tmp_mastery_db(tmp_path: Path) -> Path:
    """
    Create a temporary mastery SQLite database with FSRS schema.

    Args:
        tmp_path: Pytest's temporary directory fixture

    Returns:
        Path to the temporary mastery database file

    Example:
        def test_srs_scheduling(tmp_mastery_db):
            conn = sqlite3.connect(tmp_mastery_db)
            cursor = conn.execute("SELECT * FROM items WHERE stability > 1.0")
            items = cursor.fetchall()
    """
    db_path = tmp_path / "mastery_test.sqlite"

    # Use the existing schema from state/schema.sql
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            item_id TEXT PRIMARY KEY,
            node_id TEXT NOT NULL,
            type TEXT NOT NULL,
            last_review TIMESTAMP,
            stability REAL DEFAULT 0.0,
            difficulty REAL DEFAULT 5.0,
            reps INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Review history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS review_history (
            review_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id TEXT NOT NULL,
            review_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            quality INTEGER NOT NULL,
            stability_before REAL,
            stability_after REAL,
            difficulty_before REAL,
            difficulty_after REAL,
            FOREIGN KEY (item_id) REFERENCES items(item_id) ON DELETE CASCADE
        )
    """)

    # Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_node_id ON items(node_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_type ON items(type)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_items_last_review ON items(last_review)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_review_history_item_id ON review_history(item_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_review_history_time ON review_history(review_time)"
    )

    # Due items view
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS due_items AS
        SELECT
            i.item_id,
            i.node_id,
            i.type,
            i.last_review,
            i.stability,
            i.difficulty,
            i.reps,
            CASE
                WHEN i.last_review IS NULL THEN 1
                ELSE julianday('now') - julianday(i.last_review) >= i.stability
            END AS is_due
        FROM items i
        WHERE is_due = 1
        ORDER BY i.last_review ASC NULLS FIRST
    """)

    conn.commit()
    conn.close()

    return db_path


# ============================================================================
# Learner Configuration Fixtures
# ============================================================================


@pytest.fixture
def sample_learner() -> dict[str, Any]:
    """
    Provide a sample learner configuration for testing.

    Returns:
        Dictionary containing learner profile data

    Example:
        def test_learner_preferences(sample_learner):
            assert sample_learner["cefr_current"] == "A2"
            assert sample_learner["l1"] == "English"
    """
    return {
        "learner_id": "test_learner_001",
        "name": "Test User",
        "l1": "English",
        "target_language": "Spanish",
        "cefr_current": "A2",
        "cefr_goal": "B1",
        "correction_style": "implicit_recasts",
        "topics_of_interest": [
            "travel",
            "food",
            "daily_routines",
            "work",
        ],
        "session_preferences": {
            "duration_minutes": 20,
            "new_items_per_session": 3,
            "review_items_per_session": 7,
            "correction_frequency": "moderate",
        },
        "created_at": "2025-01-15T10:00:00Z",
        "last_session": "2025-01-20T14:30:00Z",
    }


@pytest.fixture
def advanced_learner() -> dict[str, Any]:
    """
    Provide an advanced learner configuration for testing edge cases.

    Returns:
        Dictionary containing advanced learner profile data
    """
    return {
        "learner_id": "test_learner_advanced",
        "name": "Advanced Test User",
        "l1": "English",
        "target_language": "Spanish",
        "cefr_current": "B2",
        "cefr_goal": "C1",
        "correction_style": "explicit",
        "topics_of_interest": [
            "politics",
            "economics",
            "literature",
            "philosophy",
        ],
        "session_preferences": {
            "duration_minutes": 30,
            "new_items_per_session": 5,
            "review_items_per_session": 10,
            "correction_frequency": "high",
        },
        "created_at": "2023-01-01T10:00:00Z",
        "last_session": "2025-01-20T15:00:00Z",
    }


# ============================================================================
# Knowledge Graph Node Fixtures
# ============================================================================


@pytest.fixture
def sample_nodes() -> list[dict[str, Any]]:
    """
    Provide sample knowledge graph nodes for testing.

    Returns:
        List of node dictionaries with various types and CEFR levels

    Example:
        def test_node_structure(sample_nodes):
            assert len(sample_nodes) > 0
            assert all("node_id" in node for node in sample_nodes)
    """
    return [
        {
            "node_id": "lexeme.es.ser",
            "type": "Lexeme",
            "label": "ser (to be - permanent/essential)",
            "diagnostics": '{"forms": ["soy", "eres", "es", "somos", "sois", "son"], "usage": "permanent states, identity, origin"}',
            "prompts": '["Describe yourself using ser", "Say where you are from"]',
            "cefr_level": "A1",
            "metadata": '{"frequency": "very_high", "irregularity": "high"}',
        },
        {
            "node_id": "lexeme.es.estar",
            "type": "Lexeme",
            "label": "estar (to be - temporary/location)",
            "diagnostics": '{"forms": ["estoy", "estás", "está", "estamos", "estáis", "están"], "usage": "temporary states, location, conditions"}',
            "prompts": '["Say how you are feeling", "Tell where something is located"]',
            "cefr_level": "A1",
            "metadata": '{"frequency": "very_high", "irregularity": "high"}',
        },
        {
            "node_id": "constr.es.subjunctive_present",
            "type": "Construction",
            "label": "Present Subjunctive",
            "diagnostics": '{"form": "stem + subjunctive endings", "function": "express doubt, desire, emotion, uncertainty"}',
            "prompts": '["Express doubt about the weather", "Say what you want someone to do", "Express emotion about a situation"]',
            "cefr_level": "B1",
            "metadata": '{"complexity": "high", "error_prone": true}',
        },
        {
            "node_id": "constr.es.preterite_vs_imperfect",
            "type": "Construction",
            "label": "Preterite vs Imperfect",
            "diagnostics": '{"distinction": "completed vs ongoing past", "function": "aspect marking in past tense"}',
            "prompts": '["Tell a story using both tenses", "Describe what you were doing when something happened"]',
            "cefr_level": "A2",
            "metadata": '{"complexity": "medium", "error_prone": true}',
        },
        {
            "node_id": "morph.es.subjunctive_endings",
            "type": "Morph",
            "label": "Subjunctive Verb Endings",
            "diagnostics": '{"ar_verbs": "-e, -es, -e, -emos, -éis, -en", "er_ir_verbs": "-a, -as, -a, -amos, -áis, -an"}',
            "prompts": '["Conjugate hablar in subjunctive", "Conjugate comer in subjunctive"]',
            "cefr_level": "B1",
            "metadata": '{"type": "inflection"}',
        },
        {
            "node_id": "function.es.express_doubt",
            "type": "Function",
            "label": "Expressing Doubt",
            "diagnostics": '{"triggers": "no creo que, dudo que, es posible que", "mood": "subjunctive"}',
            "prompts": '["Express doubt about a claim", "Say you are not sure about something"]',
            "cefr_level": "B1",
            "metadata": '{"communicative_function": true}',
        },
        {
            "node_id": "cando.es.introduce_self_A1",
            "type": "CanDo",
            "label": "Can introduce self and ask basic questions",
            "diagnostics": '{"examples": ["Me llamo...", "¿Cómo te llamas?", "Soy de..."]}',
            "prompts": '["Introduce yourself to a new person", "Ask someone their name and where they are from"]',
            "cefr_level": "A1",
            "metadata": '{"skill": "interaction"}',
        },
        {
            "node_id": "topic.es.food_ordering",
            "type": "Topic",
            "label": "Ordering Food at a Restaurant",
            "diagnostics": '{"vocabulary": ["menú", "plato", "cuenta"], "structures": ["Quisiera...", "Para mí..."]}',
            "prompts": '["Order a meal at a restaurant", "Ask for the bill"]',
            "cefr_level": "A2",
            "metadata": '{"domain": "transactional"}',
        },
    ]


@pytest.fixture
def sample_edges() -> list[dict[str, Any]]:
    """
    Provide sample knowledge graph edges showing relationships.

    Returns:
        List of edge dictionaries with various relationship types

    Example:
        def test_prerequisite_chain(sample_edges):
            prereqs = [e for e in sample_edges if e["edge_type"] == "prerequisite_of"]
            assert len(prereqs) > 0
    """
    return [
        {
            "source_id": "lexeme.es.ser",
            "target_id": "cando.es.introduce_self_A1",
            "edge_type": "prerequisite_of",
            "weight": 1.0,
            "metadata": '{"required": true}',
        },
        {
            "source_id": "lexeme.es.estar",
            "target_id": "cando.es.introduce_self_A1",
            "edge_type": "prerequisite_of",
            "weight": 1.0,
            "metadata": '{"required": true}',
        },
        {
            "source_id": "morph.es.subjunctive_endings",
            "target_id": "constr.es.subjunctive_present",
            "edge_type": "prerequisite_of",
            "weight": 1.0,
            "metadata": '{"required": true}',
        },
        {
            "source_id": "constr.es.subjunctive_present",
            "target_id": "function.es.express_doubt",
            "edge_type": "realizes",
            "weight": 0.8,
            "metadata": '{"usage_context": "doubt_expressions"}',
        },
        {
            "source_id": "lexeme.es.ser",
            "target_id": "lexeme.es.estar",
            "edge_type": "contrasts_with",
            "weight": 1.0,
            "metadata": '{"common_confusion": true}',
        },
        {
            "source_id": "function.es.express_doubt",
            "target_id": "constr.es.subjunctive_present",
            "edge_type": "depends_on",
            "weight": 1.0,
            "metadata": '{"grammatical_dependency": true}',
        },
        {
            "source_id": "topic.es.food_ordering",
            "target_id": "constr.es.subjunctive_present",
            "edge_type": "practice_with",
            "weight": 0.5,
            "metadata": '{"context": "polite_requests"}',
        },
    ]


@pytest.fixture
def populated_kg_db(tmp_kg_db: Path, sample_nodes: list[dict[str, Any]], sample_edges: list[dict[str, Any]]) -> Path:
    """
    Create a KG database pre-populated with sample nodes and edges.

    Args:
        tmp_kg_db: Empty KG database fixture
        sample_nodes: Sample node data
        sample_edges: Sample edge data

    Returns:
        Path to populated KG database

    Example:
        def test_query_nodes(populated_kg_db):
            conn = sqlite3.connect(populated_kg_db)
            cursor = conn.execute("SELECT COUNT(*) FROM nodes")
            count = cursor.fetchone()[0]
            assert count > 0
    """
    conn = sqlite3.connect(tmp_kg_db)
    cursor = conn.cursor()

    # Insert sample nodes
    for node in sample_nodes:
        cursor.execute(
            """
            INSERT INTO nodes (node_id, type, label, diagnostics, prompts, cefr_level, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                node["node_id"],
                node["type"],
                node["label"],
                node.get("diagnostics", "{}"),
                node.get("prompts", "[]"),
                node.get("cefr_level", "A1"),
                node.get("metadata", "{}"),
            ),
        )

    # Insert sample edges
    for edge in sample_edges:
        cursor.execute(
            """
            INSERT INTO edges (source_id, target_id, edge_type, weight, metadata)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                edge["source_id"],
                edge["target_id"],
                edge["edge_type"],
                edge.get("weight", 1.0),
                edge.get("metadata", "{}"),
            ),
        )

    conn.commit()
    conn.close()

    return tmp_kg_db


@pytest.fixture
def populated_mastery_db(
    tmp_mastery_db: Path,
    sample_learner: dict[str, Any],
) -> Path:
    """
    Create a mastery database with sample items and review history.

    Args:
        tmp_mastery_db: Empty mastery database fixture
        sample_learner: Sample learner configuration

    Returns:
        Path to populated mastery database

    Example:
        def test_due_items(populated_mastery_db):
            conn = sqlite3.connect(populated_mastery_db)
            cursor = conn.execute("SELECT * FROM due_items")
            due = cursor.fetchall()
            assert len(due) > 0
    """
    conn = sqlite3.connect(tmp_mastery_db)
    cursor = conn.cursor()

    # Sample items at different stages
    items = [
        {
            "item_id": "item.es.ser.001",
            "node_id": "lexeme.es.ser",
            "type": "production",
            "last_review": "2025-01-20T10:00:00Z",
            "stability": 3.5,
            "difficulty": 4.2,
            "reps": 5,
        },
        {
            "item_id": "item.es.estar.001",
            "node_id": "lexeme.es.estar",
            "type": "production",
            "last_review": "2025-01-19T14:00:00Z",
            "stability": 2.1,
            "difficulty": 5.8,
            "reps": 3,
        },
        {
            "item_id": "item.es.subjunctive.001",
            "node_id": "constr.es.subjunctive_present",
            "type": "production",
            "last_review": None,  # Never reviewed
            "stability": 0.0,
            "difficulty": 5.0,
            "reps": 0,
        },
        {
            "item_id": "item.es.preterite_imperfect.001",
            "node_id": "constr.es.preterite_vs_imperfect",
            "type": "recognition",
            "last_review": "2025-01-18T09:00:00Z",
            "stability": 1.5,
            "difficulty": 6.5,
            "reps": 2,
        },
    ]

    for item in items:
        cursor.execute(
            """
            INSERT INTO items (item_id, node_id, type, last_review, stability, difficulty, reps)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item["item_id"],
                item["node_id"],
                item["type"],
                item["last_review"],
                item["stability"],
                item["difficulty"],
                item["reps"],
            ),
        )

        # Add some review history for items that have been reviewed
        if item["last_review"] is not None and item["reps"] > 0:
            for rep in range(item["reps"]):
                cursor.execute(
                    """
                    INSERT INTO review_history
                    (item_id, quality, stability_before, stability_after, difficulty_before, difficulty_after)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item["item_id"],
                        3 + (rep % 3),  # Vary quality: 3, 4, 5
                        item["stability"] - 0.5 * (item["reps"] - rep),
                        item["stability"] - 0.5 * (item["reps"] - rep - 1),
                        item["difficulty"],
                        item["difficulty"],
                    ),
                )

    conn.commit()
    conn.close()

    return tmp_mastery_db


# ============================================================================
# FSRS Parameter Fixtures
# ============================================================================


@pytest.fixture
def fsrs_default_params() -> dict[str, Any]:
    """
    Provide default FSRS algorithm parameters.

    Returns:
        Dictionary of FSRS parameters

    Example:
        def test_fsrs_calculation(fsrs_default_params):
            w = fsrs_default_params["weights"]
            assert len(w) == 17
    """
    return {
        "weights": [
            0.4072,  # w0: initial stability for Again
            1.1829,  # w1: initial stability for Hard
            3.1262,  # w2: initial stability for Good
            15.4722, # w3: initial stability for Easy
            7.2102,  # w4: difficulty decay rate
            0.5316,  # w5: difficulty gain for Again
            1.0651,  # w6: difficulty gain for Hard
            0.0234,  # w7: difficulty gain for Good
            1.616,   # w8: stability decay for Again
            0.1544,  # w9: stability decay for Hard
            1.0826,  # w10: stability decay for Good
            1.9813,  # w11: stability decay for Easy
            0.0953,  # w12: stability gain for correct recall
            0.2975,  # w13: stability loss for incorrect recall
            2.1739,  # w14: stability decay factor
            0.3246,  # w15: difficulty weight in stability
            2.9,     # w16: decay exponent
        ],
        "request_retention": 0.9,  # Target retention rate
        "maximum_interval": 36500,  # Maximum interval in days (100 years)
        "enable_fuzz": True,        # Add randomization to intervals
        "enable_short_term": True,  # Use short-term scheduling
    }


# ============================================================================
# YAML Test Data Fixtures
# ============================================================================


@pytest.fixture
def sample_kg_yaml(tmp_path: Path) -> Path:
    """
    Create a sample KG YAML file for testing KG building.

    Args:
        tmp_path: Pytest's temporary directory fixture

    Returns:
        Path to sample YAML file

    Example:
        def test_yaml_parsing(sample_kg_yaml):
            with open(sample_kg_yaml) as f:
                data = yaml.safe_load(f)
            assert "nodes" in data
    """
    yaml_content = """
nodes:
  - id: lexeme.es.hola
    type: Lexeme
    label: hola (hello)
    cefr_level: A1
    diagnostics:
      form: "hola"
      function: "greeting"
    prompts:
      - "Greet someone you meet"
      - "Say hello in Spanish"

  - id: lexeme.es.gracias
    type: Lexeme
    label: gracias (thank you)
    cefr_level: A1
    diagnostics:
      form: "gracias"
      function: "expressing gratitude"
    prompts:
      - "Thank someone for help"

edges:
  - source: lexeme.es.hola
    target: cando.es.basic_greetings_A1
    type: prerequisite_of
    weight: 1.0

  - source: lexeme.es.gracias
    target: cando.es.basic_politeness_A1
    type: prerequisite_of
    weight: 1.0
"""
    yaml_path = tmp_path / "test_kg.yaml"
    yaml_path.write_text(yaml_content)
    return yaml_path


# ============================================================================
# Mock MCP Context Fixtures
# ============================================================================


@pytest.fixture
def mock_mcp_context() -> dict[str, Any]:
    """
    Provide a mock MCP server context for testing tools.

    Returns:
        Dictionary representing MCP context state

    Example:
        def test_mcp_tool(mock_mcp_context):
            result = kg_next(mock_mcp_context, learner_id="test", k=5)
            assert isinstance(result, str)
    """
    return {
        "kg_db_path": None,  # Will be set by test
        "mastery_db_path": None,  # Will be set by test
        "config": {
            "max_results": 100,
            "default_k": 5,
            "cache_enabled": False,
        },
    }
