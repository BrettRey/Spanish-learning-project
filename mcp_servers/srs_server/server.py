"""
SRS MCP Server Implementation.

This module implements the MCP server for the Spaced Repetition System,
providing tools for managing learning schedules using the FSRS algorithm.

FSRS (Free Spaced Repetition Scheduler) is a modern alternative to SM-2,
using a memory model based on DSR (Difficulty, Stability, Retrievability).
"""

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from state.fsrs import ReviewCard, ReviewResult, review_card, DEFAULT_W

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class FSRSParameters:
    """
    FSRS algorithm parameters for a single item.

    Attributes:
        stability: Current memory stability (in days)
        difficulty: Item difficulty (0-10, higher = harder)
        elapsed_days: Days since last review
        scheduled_days: Days until next review
        reps: Number of times reviewed
        lapses: Number of times forgotten
        state: Current state (0=new, 1=learning, 2=review, 3=relearning)
    """
    stability: float
    difficulty: float
    elapsed_days: int
    scheduled_days: int
    reps: int
    lapses: int
    state: int


@dataclass
class ReviewItem:
    """
    A single item due for review.

    Attributes:
        item_id: Unique identifier for the item
        node_id: Knowledge graph node this item relates to
        type: Type of review (production, recognition, etc.)
        last_review: ISO timestamp of last review
        due_date: ISO timestamp when item is due
        fsrs_params: Current FSRS parameters
    """
    item_id: str
    node_id: str
    type: str
    last_review: str
    due_date: str
    fsrs_params: FSRSParameters


@dataclass
class LearnerStats:
    """
    Learning statistics for a learner.

    Attributes:
        learner_id: Unique learner identifier
        total_items: Total number of items in system
        due_count: Number of items currently due
        new_count: Number of new (never reviewed) items
        learning_count: Items in learning state
        review_count: Items in review state
        mastered_count: Items with high stability (>30 days)
        average_difficulty: Mean difficulty across all items
        reviews_today: Number of reviews completed today
        streak_days: Consecutive days with reviews
    """
    learner_id: str
    total_items: int
    due_count: int
    new_count: int
    learning_count: int
    review_count: int
    mastered_count: int
    average_difficulty: float
    reviews_today: int
    streak_days: int


class SRSServer:
    """
    Main SRS MCP Server class.

    This server provides three primary tools:
    1. srs.due - Get items due for review
    2. srs.update - Update FSRS parameters after a review
    3. srs.stats - Get learner statistics

    Currently uses mock data; designed for future SQLite integration.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize the SRS server.

        Args:
            db_path: Path to mastery.sqlite database (defaults to ../state/mastery.sqlite)
        """
        self.db_path = db_path or Path(__file__).parent.parent.parent / "state" / "mastery.sqlite"

        if not self.db_path.exists():
            # If the database doesn't exist, create it and its schema
            logger.info(f"Mastery database not found at {self.db_path}, creating new one.")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS review_items (
                    item_id TEXT PRIMARY KEY,
                    learner_id TEXT NOT NULL,
                    node_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    last_review TIMESTAMP,
                    next_review TIMESTAMP NOT NULL,
                    stability REAL NOT NULL,
                    difficulty REAL NOT NULL,
                    reps INTEGER NOT NULL,
                    lapses INTEGER NOT NULL,
                    state INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_review_items_learner ON review_items(learner_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_review_items_next_review ON review_items(next_review)")
            conn.commit()
            conn.close()
        
        logger.info(f"SRSServer initialized with db_path={self.db_path}")



    def _query_due_items(self, learner_id: str, limit: int) -> List[ReviewItem]:
        """
        Query the mastery database for items due for review for a given learner.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            now = datetime.now(timezone.utc)

            cursor.execute(
                """
                SELECT
                    item_id, node_id, type, last_review, next_review,
                    stability, difficulty, reps, lapses, state
                FROM review_items
                WHERE learner_id = ? AND next_review <= ?
                ORDER BY next_review ASC
                LIMIT ?
                """,
                (learner_id, now.isoformat(), limit)
            )
            rows = cursor.fetchall()

        due_items: List[ReviewItem] = []
        for row in rows:
            fsrs_params = FSRSParameters(
                stability=row["stability"],
                difficulty=row["difficulty"],
                elapsed_days=(now - datetime.fromisoformat(row["last_review"])).days if row["last_review"] else 0,
                scheduled_days=(datetime.fromisoformat(row["next_review"]) - now).days,
                reps=row["reps"],
                lapses=row["lapses"],
                state=row["state"]
            )
            due_items.append(
                ReviewItem(
                    item_id=row["item_id"],
                    node_id=row["node_id"],
                    type=row["type"],
                    last_review=row["last_review"],
                    due_date=row["next_review"],
                    fsrs_params=fsrs_params
                )
            )
        return due_items

    def _update_srs_item(
        self,
        item_id: str,
        learner_id: str,
        node_id: str,
        item_type: str,
        new_params: FSRSParameters,
        review_time: datetime,
        next_review_date: datetime,
    ) -> None:
        """
        Update or insert an SRS item in the database.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO review_items (
                    item_id, learner_id, node_id, type, last_review, next_review,
                    stability, difficulty, reps, lapses, state
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(item_id) DO UPDATE SET
                    learner_id = excluded.learner_id,
                    node_id = excluded.node_id,
                    type = excluded.type,
                    last_review = excluded.last_review,
                    next_review = excluded.next_review,
                    stability = excluded.stability,
                    difficulty = excluded.difficulty,
                    reps = excluded.reps,
                    lapses = excluded.lapses,
                    state = excluded.state
                """,
                (
                    item_id,
                    learner_id,
                    node_id,
                    item_type,
                    review_time.isoformat(),
                    next_review_date.isoformat(),
                    new_params.stability, new_params.difficulty, new_params.reps, new_params.lapses, new_params.state
                )
            )
            conn.commit()

    def _query_learner_stats(self, learner_id: str) -> LearnerStats:
        """
        Query the mastery database for learner statistics.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            now = datetime.now(timezone.utc)

            # Total items
            cursor.execute("SELECT COUNT(*) FROM review_items WHERE learner_id = ?", (learner_id,))
            total_items = cursor.fetchone()[0]

            # Due count
            cursor.execute("SELECT COUNT(*) FROM review_items WHERE learner_id = ? AND next_review <= ?", (learner_id, now.isoformat()))
            due_count = cursor.fetchone()[0]

            # New count (reps = 0)
            cursor.execute("SELECT COUNT(*) FROM review_items WHERE learner_id = ? AND reps = 0", (learner_id,))
            new_count = cursor.fetchone()[0]

            # Learning count (state = 1 or 3)
            cursor.execute("SELECT COUNT(*) FROM review_items WHERE learner_id = ? AND (state = 1 OR state = 3)", (learner_id,))
            learning_count = cursor.fetchone()[0]

            # Review count (state = 2)
            cursor.execute("SELECT COUNT(*) FROM review_items WHERE learner_id = ? AND state = 2", (learner_id,))
            review_count = cursor.fetchone()[0]

            # Mastered count (stability > 30 days, arbitrary threshold for now)
            cursor.execute("SELECT COUNT(*) FROM review_items WHERE learner_id = ? AND stability > 30", (learner_id,))
            mastered_count = cursor.fetchone()[0]

            # Average difficulty
            cursor.execute("SELECT AVG(difficulty) FROM review_items WHERE learner_id = ?", (learner_id,))
            avg_difficulty = cursor.fetchone()[0]
            average_difficulty = round(avg_difficulty, 2) if avg_difficulty else 0.0

            # Reviews today (assuming last_review is updated on every review)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            cursor.execute("SELECT COUNT(*) FROM review_items WHERE learner_id = ? AND last_review >= ?", (learner_id, today_start))
            reviews_today = cursor.fetchone()[0]

            # Streak days (more complex, placeholder for now)
            streak_days = 0 # TODO: Implement proper streak calculation

        return LearnerStats(
            learner_id=learner_id,
            total_items=total_items,
            due_count=due_count,
            new_count=new_count,
            learning_count=learning_count,
            review_count=review_count,
            mastered_count=mastered_count,
            average_difficulty=average_difficulty,
            reviews_today=reviews_today,
            streak_days=streak_days
        )

    def get_due_items(self, learner_id: str, limit: int = 10) -> str:
        """
        MCP Tool: srs.due

        Retrieve items due for review for a given learner.

        Args:
            learner_id: The learner's unique identifier
            limit: Maximum number of items to return (default: 10)

        Returns:
            JSON string containing list of due items

        Example:
            >>> server.get_due_items("brett", limit=5)
            '{"items": [...], "count": 3}'
        """
        try:
            logger.info(f"Getting due items for learner_id={learner_id}, limit={limit}")

            # Validate inputs
            if not learner_id or not isinstance(learner_id, str):
                return json.dumps({
                    "error": "Invalid learner_id",
                    "message": "learner_id must be a non-empty string"
                })

            if limit <= 0 or limit > 100:
                return json.dumps({
                    "error": "Invalid limit",
                    "message": "limit must be between 1 and 100"
                })

            # Get items from database
            items = self._query_due_items(learner_id, limit)

            # Convert to serializable format
            items_dict = [
                {
                    "item_id": item.item_id,
                    "node_id": item.node_id,
                    "type": item.type,
                    "last_review": item.last_review,
                    "due_date": item.due_date,
                    "fsrs_params": asdict(item.fsrs_params)
                }
                for item in items
            ]

            result = {
                "items": items_dict,
                "count": len(items_dict),
                "learner_id": learner_id
            }

            logger.info(f"Returning {len(items_dict)} due items")
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error in get_due_items: {e}", exc_info=True)
            return json.dumps({
                "error": "Internal error",
                "message": str(e)
            })

    def update_item(self, item_id: str, quality: int) -> str:
        """
        MCP Tool: srs.update

        Update FSRS parameters for an item after a review.

        Args:
            item_id: The item's unique identifier
            quality: Review quality (0-5)
                    0: Complete blackout
                    1: Incorrect, but familiar
                    2: Correct with serious difficulty
                    3: Correct with some difficulty
                    4: Correct with ease
                    5: Perfect recall

        Returns:
            JSON string with updated parameters

        Example:
            >>> server.update_item("card.es.ser_vs_estar.001", quality=4)
            '{"success": true, "next_review_date": "2025-11-12T10:00:00Z"}'
        """
        try:
            logger.info(f"Updating item_id={item_id} with quality={quality}")

            # Validate inputs
            if not item_id or not isinstance(item_id, str):
                return json.dumps({
                    "error": "Invalid item_id",
                    "message": "item_id must be a non-empty string"
                })

            if not isinstance(quality, int) or quality < 0 or quality > 5:
                return json.dumps({
                    "error": "Invalid quality",
                    "message": "quality must be an integer between 0 and 5"
                })

            # Fetch current params from database or initialize if new
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM review_items WHERE item_id = ?",
                    (item_id,)
                )
                row = cursor.fetchone()

            if row:
                # Convert database row to ReviewCard
                current_card = ReviewCard(
                    stability=row["stability"],
                    difficulty=row["difficulty"],
                    reps=row["reps"],
                    last_review=datetime.fromisoformat(row["last_review"]) if row["last_review"] else None
                )
                learner_id = row["learner_id"]
                node_id = row["node_id"]
                item_type = row["type"]
                previous_review_time = current_card.last_review
            else:
                # If item is new, initialize with default FSRS parameters
                # This assumes that new items are created with a default learner_id, node_id, and type.
                # In a real system, these would be passed in or derived.
                # For now, we'll use placeholder values and assume the item_id is unique.
                logger.warning(f"Item {item_id} not found, initializing with default FSRS parameters.")
                current_card = ReviewCard(
                    stability=0.0, difficulty=0.0, reps=0, last_review=None
                )
                learner_id = "default_learner"
                node_id = "default_node"
                item_type = "default_type"
                previous_review_time = None

            # Process review using the full FSRS algorithm
            review_timestamp = datetime.now(timezone.utc)
            updated_card, review_result = review_card(
                current_card,
                quality,
                review_time=review_timestamp,
                w=DEFAULT_W,
            )

            # Convert updated_card back to FSRSParameters for storage
            existing_lapses = row["lapses"] if row else 0
            new_lapses = existing_lapses + (1 if quality < 3 else 0)

            new_params = FSRSParameters(
                stability=updated_card.stability,
                difficulty=updated_card.difficulty,
                elapsed_days=(
                    (review_timestamp - previous_review_time).days
                    if previous_review_time
                    else 0
                ),
                scheduled_days=(review_result.next_review_date - review_timestamp).days,
                reps=updated_card.reps,
                lapses=new_lapses,
                state=2 # Assuming review state after update
            )

            # Save to database
            self._update_srs_item(
                item_id,
                learner_id,
                node_id,
                item_type,
                new_params,
                review_timestamp,
                review_result.next_review_date,
            )

            result = {
                "success": True,
                "item_id": item_id,
                "quality": quality,
                "updated_params": asdict(new_params),
                "next_review_date": review_result.next_review_date.isoformat(),
                "days_until_next": new_params.scheduled_days
            }

            logger.info(f"Updated successfully. Next review in {new_params.scheduled_days} days")
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error in update_item: {e}", exc_info=True)
            return json.dumps({
                "error": "Internal error",
                "message": str(e)
            })

    def get_stats(self, learner_id: str) -> str:
        """
        MCP Tool: srs.stats

        Get learning statistics for a learner.

        Args:
            learner_id: The learner's unique identifier

        Returns:
            JSON string with comprehensive learner statistics

        Example:
            >>> server.get_stats("brett")
            '{"learner_id": "brett", "total_items": 247, ...}'
        """
        try:
            logger.info(f"Getting stats for learner_id={learner_id}")

            # Validate inputs
            if not learner_id or not isinstance(learner_id, str):
                return json.dumps({
                    "error": "Invalid learner_id",
                    "message": "learner_id must be a non-empty string"
                })

            # Get stats from database
            stats = self._query_learner_stats(learner_id)

            result = asdict(stats)

            logger.info(f"Returning stats for {learner_id}")
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error in get_stats: {e}", exc_info=True)
            return json.dumps({
                "error": "Internal error",
                "message": str(e)
            })


# MCP Tool Registration
# When integrated with full MCP framework, these would be registered as tools
def register_tools(server: SRSServer) -> Dict[str, Any]:
    """
    Register MCP tools with their metadata.

    Args:
        server: SRSServer instance

    Returns:
        Dictionary of tool definitions
    """
    return {
        "srs.due": {
            "function": server.get_due_items,
            "description": "Return items due for review",
            "parameters": {
                "learner_id": {
                    "type": "string",
                    "description": "Unique learner identifier",
                    "required": True
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of items to return (1-100)",
                    "default": 10,
                    "required": False
                }
            }
        },
        "srs.update": {
            "function": server.update_item,
            "description": "Update FSRS parameters after a review",
            "parameters": {
                "item_id": {
                    "type": "string",
                    "description": "Unique item identifier",
                    "required": True
                },
                "quality": {
                    "type": "integer",
                    "description": "Review quality (0-5: blackout to perfect)",
                    "required": True
                }
            }
        },
        "srs.stats": {
            "function": server.get_stats,
            "description": "Get learning statistics for a learner",
            "parameters": {
                "learner_id": {
                    "type": "string",
                    "description": "Unique learner identifier",
                    "required": True
                }
            }
        }
    }
