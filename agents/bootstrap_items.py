#!/usr/bin/env python3
"""
Bootstrap Items from Knowledge Graph

Creates initial items in the mastery database for all KG nodes
that don't have corresponding items yet.

This is needed for new learners or when expanding the KG.
"""

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def infer_skill(node_type: str, strand: str) -> str:
    """
    Infer primary skill from node type and strand.

    Following Nation's Four Strands framework:
    - Meaning-input → reading or listening (default reading for Topics)
    - Meaning-output → speaking or writing (default speaking for CanDo/Function)
    - Language-focused → writing (explicit form study)
    - Fluency → speaking (default for speed drills)

    Args:
        node_type: Type of KG node (Lexeme, Construction, etc.)
        strand: Primary strand (meaning_input, meaning_output, etc.)

    Returns:
        Skill name: 'reading', 'listening', 'speaking', 'writing'
    """
    # Topic nodes are comprehension-focused (reading by default)
    if node_type == "Topic":
        return "reading"  # Could be "listening" if audio material

    # Meaning-output: communicative production
    if strand == "meaning_output":
        if node_type in ["CanDo", "Function", "DiscourseMove", "PragmaticCue"]:
            return "speaking"  # Default for communicative tasks
        return "writing"  # Fallback

    # Language-focused: form study (written practice default)
    if strand == "language_focused":
        return "writing"  # Grammar/vocabulary study

    # Fluency: automaticity practice (speaking default)
    if strand == "fluency":
        return "speaking"

    # Meaning-input: comprehension
    if strand == "meaning_input":
        return "reading"  # Default; could be listening

    # Default fallback
    return "writing"


def bootstrap_items_from_kg(
    kg_db_path: Path = Path("kg.sqlite"),
    mastery_db_path: Path = Path("state/mastery.sqlite"),
    default_strand: str = "meaning_output",
) -> int:
    """
    Create items for all KG nodes that don't have items yet.

    Args:
        kg_db_path: Path to knowledge graph database
        mastery_db_path: Path to mastery database
        default_strand: Default strand for new items

    Returns:
        Number of items created
    """

    # Get all KG nodes
    kg_conn = sqlite3.connect(kg_db_path)
    kg_cursor = kg_conn.cursor()
    kg_cursor.execute("SELECT node_id, type, label FROM nodes")
    kg_nodes = kg_cursor.fetchall()
    kg_conn.close()

    print(f"Found {len(kg_nodes)} nodes in knowledge graph")

    # Get existing items
    mastery_conn = sqlite3.connect(mastery_db_path)
    mastery_cursor = mastery_conn.cursor()
    mastery_cursor.execute("SELECT DISTINCT node_id FROM items")
    existing_node_ids = set(row[0] for row in mastery_cursor.fetchall())

    print(f"Found {len(existing_node_ids)} nodes with existing items")

    # Create items for nodes without items
    items_created = 0
    now = datetime.now().isoformat()

    for node_id, node_type, label in kg_nodes:
        if node_id in existing_node_ids:
            continue

        # Determine strand based on node type
        if node_type == "Lexeme":
            strand = "language_focused"
        elif node_type == "Construction":
            strand = "language_focused"
        elif node_type == "Morph":
            strand = "language_focused"
        elif node_type.startswith("cando"):
            strand = "meaning_output"
        elif node_type == "Function":
            strand = "meaning_output"
        elif node_type == "DiscourseMove":
            strand = "meaning_output"
        elif node_type == "PragmaticCue":
            strand = "meaning_output"
        elif node_type == "AssessmentCriterion":
            strand = "meaning_output"
        elif node_type == "Topic":
            strand = "meaning_input"
        else:
            strand = default_strand

        # Infer skill from node type and strand
        skill = infer_skill(node_type, strand)

        # Create item_id (node_id + .001 suffix for first card)
        item_id = f"{node_id}.001"

        # Insert new item with default FSRS parameters
        mastery_cursor.execute(
            """
            INSERT INTO items (
                item_id,
                node_id,
                type,
                last_review,
                stability,
                difficulty,
                reps,
                created_at,
                primary_strand,
                skill,
                mastery_status,
                last_mastery_check
            ) VALUES (?, ?, ?, NULL, 0.0, 5.0, 0, ?, ?, ?, 'new', ?)
        """,
            (
                item_id,
                node_id,
                "production",  # Default type
                now,
                strand,
                skill,
                now,
            ),
        )

        items_created += 1
        print(f"  Created: {item_id} ({strand}, {skill}) - {label}")

    mastery_conn.commit()
    mastery_conn.close()

    print(f"\n✅ Created {items_created} new items")
    return items_created


def main():
    """Bootstrap items from command line."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Bootstrap mastery items from knowledge graph"
    )
    parser.add_argument(
        "--kg-db",
        type=Path,
        default=Path("kg.sqlite"),
        help="Path to knowledge graph database",
    )
    parser.add_argument(
        "--mastery-db",
        type=Path,
        default=Path("state/mastery.sqlite"),
        help="Path to mastery database",
    )
    parser.add_argument(
        "--strand",
        default="meaning_output",
        help="Default strand for new items",
    )

    args = parser.parse_args()

    if not args.kg_db.exists():
        print(f"Error: KG database not found: {args.kg_db}")
        sys.exit(1)

    if not args.mastery_db.exists():
        print(f"Error: Mastery database not found: {args.mastery_db}")
        sys.exit(1)

    items_created = bootstrap_items_from_kg(
        kg_db_path=args.kg_db,
        mastery_db_path=args.mastery_db,
        default_strand=args.strand,
    )

    sys.exit(0 if items_created > 0 else 1)


if __name__ == "__main__":
    main()
