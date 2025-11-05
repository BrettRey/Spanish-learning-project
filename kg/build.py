#!/usr/bin/env python3
"""
Knowledge Graph Builder

Compiles YAML seed files into a SQLite database with nodes and edges.
Supports the Spanish language learning system's knowledge graph model.

Usage:
    python kg/build.py <input_dir> <output_db>

Example:
    python kg/build.py kg/seed kg.sqlite
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence

import yaml


def create_schema(conn: sqlite3.Connection) -> None:
    """
    Create the knowledge graph database schema.

    Tables:
    - nodes: Stores linguistic items with their metadata
    - edges: Stores relationships between nodes
    - evidence: Aggregated practice evidence per node (global placeholder)

    Args:
        conn: SQLite database connection
    """
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS nodes (
            node_id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            label TEXT NOT NULL,
            cefr_level TEXT,
            diagnostics TEXT,
            prompts TEXT,
            metadata TEXT,
            data_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
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
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS evidence (
            evidence_id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT NOT NULL,
            learner_id TEXT NOT NULL,
            success_count INTEGER DEFAULT 0,
            error_count INTEGER DEFAULT 0,
            last_practiced TIMESTAMP,
            FOREIGN KEY (node_id) REFERENCES nodes(node_id) ON DELETE CASCADE,
            UNIQUE (node_id, learner_id)
        )
        """
    )

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_nodes_cefr ON nodes(cefr_level)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_type ON edges(edge_type)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_evidence_learner ON evidence(learner_id)"
    )

    conn.commit()


def parse_yaml_file(file_path: Path) -> Dict[str, Any]:
    """
    Parse a YAML file containing node definition.

    Args:
        file_path: Path to the YAML file

    Returns:
        Dictionary containing node data

    Raises:
        ValueError: If YAML file is invalid or missing required fields
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not data:
            raise ValueError(f"Empty YAML file: {file_path}")

        # Validate required fields
        required_fields = ['id', 'type', 'label']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(
                f"Missing required fields in {file_path}: {', '.join(missing_fields)}"
            )

        return data

    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {file_path}: {e}")


def extract_edges(node_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract edge relationships from node data.

    Looks for fields like 'prerequisites', 'can_do', 'contrasts_with', etc.
    and converts them into edge tuples.

    Args:
        node_data: Dictionary containing node information

    Returns:
        List of (from_id, to_id, edge_type) tuples
    """
    edges: List[Dict[str, Any]] = []
    node_id = node_data["id"]

    # Map of field names to edge types
    edge_mappings = {
        "prerequisites": "prerequisite_of",
        "can_do": "realizes",
        "contrasts_with": "contrasts_with",
        "depends_on": "depends_on",
        "practice_with": "practice_with",
        "addresses_error": "addresses_error",
    }

    for field, edge_type in edge_mappings.items():
        if field in node_data and node_data[field]:
            target_ids: Sequence[str] | str = node_data[field]
            if not isinstance(target_ids, list):
                target_ids = [target_ids]

            for target_id in target_ids:
                if field == "prerequisites":
                    edges.append(
                        {
                            "source_id": target_id,
                            "target_id": node_id,
                            "edge_type": edge_type,
                        }
                    )
                else:
                    edges.append(
                        {
                            "source_id": node_id,
                            "target_id": target_id,
                            "edge_type": edge_type,
                        }
                    )

    return edges


def insert_node(conn: sqlite3.Connection, node_data: Dict[str, Any]) -> None:
    """
    Insert a node into the database.

    Args:
        conn: SQLite database connection
        node_data: Dictionary containing node information
    """
    cursor = conn.cursor()

    node_id = node_data["id"]
    node_type = node_data["type"]
    label = node_data["label"]
    cefr_level = node_data.get("cefr_level")

    diagnostics = node_data.get("diagnostics")
    if diagnostics is not None:
        diagnostics = json.dumps(diagnostics, ensure_ascii=False)

    prompts = node_data.get("prompts")
    if prompts is not None:
        prompts = json.dumps(prompts, ensure_ascii=False)

    known_keys = {
        "id",
        "type",
        "label",
        "cefr_level",
        "prerequisites",
        "can_do",
        "contrasts_with",
        "depends_on",
        "practice_with",
        "addresses_error",
        "diagnostics",
        "prompts",
    }
    metadata = {
        key: value for key, value in node_data.items() if key not in known_keys
    }
    metadata_json = (
        json.dumps(metadata, ensure_ascii=False) if metadata else None
    )

    data_json = json.dumps(node_data, ensure_ascii=False)

    cursor.execute(
        """
        INSERT OR REPLACE INTO nodes (
            node_id,
            type,
            label,
            cefr_level,
            diagnostics,
            prompts,
            metadata,
            data_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            node_id,
            node_type,
            label,
            cefr_level,
            diagnostics,
            prompts,
            metadata_json,
            data_json,
        ),
    )


def insert_edges(conn: sqlite3.Connection, edges: List[tuple]) -> None:
    """
    Insert edges into the database.

    Args:
        conn: SQLite database connection
        edges: List of (from_id, to_id, edge_type) tuples
    """
    cursor = conn.cursor()
    cursor.executemany(
        """
        INSERT OR IGNORE INTO edges (source_id, target_id, edge_type)
        VALUES (:source_id, :target_id, :edge_type)
        """,
        edges,
    )


def build_knowledge_graph(input_dir: Path, output_db: Path) -> None:
    """
    Build the knowledge graph database from YAML seed files.

    Args:
        input_dir: Directory containing YAML seed files
        output_db: Path to output SQLite database
    """
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    if not input_dir.is_dir():
        raise ValueError(f"Input path is not a directory: {input_dir}")

    # Find all YAML files
    yaml_files = list(input_dir.glob("*.yaml")) + list(input_dir.glob("*.yml"))

    if not yaml_files:
        print(f"Warning: No YAML files found in {input_dir}", file=sys.stderr)

    print(f"Found {len(yaml_files)} YAML file(s) in {input_dir}")

    # Create/open database
    conn = sqlite3.connect(output_db)

    try:
        # Create schema
        create_schema(conn)
        print(f"Created database schema in {output_db}")

        # Process each YAML file
        all_edges = []
        nodes_processed = 0

        for yaml_file in sorted(yaml_files):
            try:
                print(f"Processing {yaml_file.name}...", end=" ")
                node_data = parse_yaml_file(yaml_file)

                # Insert node
                insert_node(conn, node_data)

                # Extract edges for later insertion
                edges = extract_edges(node_data)
                all_edges.extend(edges)

                nodes_processed += 1
                print(f"OK (node: {node_data['id']})")

            except Exception as e:
                print(f"ERROR: {e}", file=sys.stderr)

        # Insert all edges
        if all_edges:
            insert_edges(conn, all_edges)
            print(f"Inserted {len(all_edges)} edge(s)")

        conn.commit()
        print(f"\nSuccessfully built knowledge graph:")
        print(f"  - {nodes_processed} nodes")
        print(f"  - {len(all_edges)} edges")
        print(f"  - Output: {output_db}")

    finally:
        conn.close()


def main() -> int:
    """
    Main entry point for the build script.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        description="Build knowledge graph database from YAML seed files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python kg/build.py kg/seed kg.sqlite
  python kg/build.py data/nodes output/graph.db
        """
    )

    parser.add_argument(
        "input_dir",
        type=Path,
        help="Directory containing YAML seed files"
    )

    parser.add_argument(
        "output_db",
        type=Path,
        help="Output SQLite database path"
    )

    args = parser.parse_args()

    try:
        build_knowledge_graph(args.input_dir, args.output_db)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
