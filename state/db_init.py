"""
Database initialization module for the Spaced Repetition System.

This module provides functions to initialize and manage the SQLite database
for tracking learner progress and spaced repetition scheduling.
"""

import sqlite3
from pathlib import Path
from typing import Optional


def initialize_database(db_path: str = "state/mastery.sqlite") -> None:
    """
    Initialize the SRS database with the required schema.

    Creates all tables, indexes, and views defined in schema.sql.
    Safe to call multiple times (uses IF NOT EXISTS).

    Args:
        db_path: Path to the SQLite database file

    Raises:
        FileNotFoundError: If schema.sql is not found
        sqlite3.Error: If database initialization fails
    """
    # Get the directory containing this file
    current_dir = Path(__file__).parent
    schema_path = current_dir / "schema.sql"

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    # Read schema SQL
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    # Initialize database
    db_full_path = Path(db_path)
    db_full_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_full_path)
    try:
        cursor = conn.cursor()
        cursor.executescript(schema_sql)
        conn.commit()
        print(f"Database initialized successfully at: {db_full_path.absolute()}")
    except sqlite3.Error as e:
        conn.rollback()
        raise sqlite3.Error(f"Failed to initialize database: {e}")
    finally:
        conn.close()


def get_connection(db_path: str = "state/mastery.sqlite") -> sqlite3.Connection:
    """
    Get a connection to the SRS database.

    Args:
        db_path: Path to the SQLite database file

    Returns:
        sqlite3.Connection: Database connection with row factory enabled

    Raises:
        sqlite3.Error: If connection fails
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn


def add_item(
    item_id: str,
    node_id: str,
    item_type: str,
    db_path: str = "state/mastery.sqlite"
) -> None:
    """
    Add a new item to the SRS system.

    Args:
        item_id: Unique identifier for the item
        node_id: Reference to knowledge graph node
        item_type: Type of item ('vocabulary', 'grammar', 'phrase', etc.)
        db_path: Path to the SQLite database file

    Raises:
        sqlite3.IntegrityError: If item_id already exists
        sqlite3.Error: If database operation fails
    """
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO items (item_id, node_id, type)
            VALUES (?, ?, ?)
            """,
            (item_id, node_id, item_type)
        )
        conn.commit()
    finally:
        conn.close()


def get_due_items(
    limit: Optional[int] = None,
    item_type: Optional[str] = None,
    db_path: str = "state/mastery.sqlite"
) -> list[dict]:
    """
    Get items that are due for review.

    Args:
        limit: Maximum number of items to return (None for all)
        item_type: Filter by item type (None for all types)
        db_path: Path to the SQLite database file

    Returns:
        List of dictionaries containing item information
    """
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()

        query = "SELECT * FROM due_items"
        params = []

        if item_type:
            query += " WHERE type = ?"
            params.append(item_type)

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Convert Row objects to dictionaries
        return [dict(row) for row in rows]
    finally:
        conn.close()


if __name__ == "__main__":
    # Initialize database when run as a script
    initialize_database()
