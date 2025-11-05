"""
Knowledge Graph MCP Server Implementation

Provides MCP tools for querying the knowledge graph, retrieving exercise prompts,
and updating learner evidence. This server is designed to integrate with the
knowledge graph SQLite database (kg/kg.sqlite) and learner mastery data
(state/mastery.sqlite).

For now, the implementation uses mock data to enable development and testing
before the full knowledge graph is built.
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class KGServerError(Exception):
    """Base exception for KG Server errors."""
    pass


class DatabaseError(KGServerError):
    """Raised when database operations fail."""
    pass


class NodeNotFoundError(KGServerError):
    """Raised when a requested node is not found."""
    pass


class KGServer:
    """
    Knowledge Graph MCP Server

    Exposes three main tools:
    1. kg.next: Query frontier nodes (prerequisites satisfied, not yet mastered)
    2. kg.prompt: Generate exercise scaffolds for specific nodes
    3. kg.add_evidence: Update evidence counters based on learner performance

    Attributes:
        kg_db_path: Path to the knowledge graph SQLite database
        mastery_db_path: Path to the learner mastery SQLite database
        use_mock_data: Whether to use mock data (True until real DB is ready)
    """

    def __init__(
        self,
        kg_db_path: Optional[Path] = None,
        mastery_db_path: Optional[Path] = None,
    ):
        """
        Initialize the KG Server.

        Args:
            kg_db_path: Path to kg.sqlite (defaults to ../kg/kg.sqlite)
            mastery_db_path: Path to mastery.sqlite (defaults to ../state/mastery.sqlite)
        """
        self.kg_db_path = kg_db_path or Path(__file__).parent.parent.parent / "kg" / "kg.sqlite"
        self.mastery_db_path = mastery_db_path or Path(__file__).parent.parent.parent / "state" / "mastery.sqlite"

        # Validate database paths exist
        if not self.kg_db_path.exists():
            raise DatabaseError(f"Knowledge graph database not found at {self.kg_db_path}")
        if not self.mastery_db_path.exists():
            logger.warning(f"Mastery database not found at {self.mastery_db_path}, will create if needed")

    def kg_next(self, learner_id: str, k: int = 5) -> str:
        """
        MCP Tool: kg.next

        Returns the top k frontier nodes for a learner. Frontier nodes are those
        where prerequisites are satisfied but the node itself is not yet mastered.

        Args:
            learner_id: Unique identifier for the learner
            k: Number of nodes to return (default: 5)

        Returns:
            JSON string containing list of frontier nodes with metadata

        Raises:
            KGServerError: If the query fails
        """
        try:
            logger.info(f"kg.next called for learner={learner_id}, k={k}")

            if k < 1 or k > 50:
                raise KGServerError(f"Invalid k value: {k}. Must be between 1 and 50.")

            nodes = self._query_frontier_nodes(learner_id, k)

            result = {
                "learner_id": learner_id,
                "count": len(nodes),
                "nodes": nodes
            }

            logger.info(f"Returning {len(nodes)} frontier nodes for {learner_id}")
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error in kg.next: {e}")
            raise KGServerError(f"Failed to query frontier nodes: {e}")

    def kg_prompt(self, node_id: str, kind: str = "production") -> str:
        """
        MCP Tool: kg.prompt

        Returns an exercise scaffold for a specific knowledge graph node.
        Scaffolds include instructions, example prompts, target forms, and
        rubric criteria.

        Args:
            node_id: Unique identifier for the KG node
            kind: Type of exercise ("production", "recognition", "correction")

        Returns:
            JSON string containing exercise scaffold

        Raises:
            NodeNotFoundError: If the node doesn't exist
            KGServerError: If the query fails
        """
        try:
            logger.info(f"kg.prompt called for node={node_id}, kind={kind}")

            valid_kinds = ["production", "recognition", "correction"]
            if kind not in valid_kinds:
                raise KGServerError(f"Invalid kind: {kind}. Must be one of {valid_kinds}")

            prompt_data = self._query_node_prompt(node_id, kind)

            logger.info(f"Returning {kind} prompt for node {node_id}")
            return json.dumps(prompt_data, indent=2)

        except Exception as e:
            logger.error(f"Error in kg.prompt: {e}")
            raise KGServerError(f"Failed to retrieve prompt for node {node_id}: {e}")

    def kg_add_evidence(self, node_id: str, success: bool, learner_id: Optional[str] = None) -> str:
        """
        MCP Tool: kg.add_evidence

        Updates the evidence counter for a knowledge graph node based on
        learner performance. Tracks both successful and unsuccessful attempts
        to inform mastery calculations.

        Args:
            node_id: Unique identifier for the KG node
            success: Whether the learner's attempt was successful
            learner_id: Optional learner identifier (defaults to "__global__" if omitted)

        Returns:
            JSON string containing updated evidence counts

        Raises:
            NodeNotFoundError: If the node doesn't exist
            KGServerError: If the update fails
        """
        try:
            learner_key = learner_id or "__global__"
            if learner_id is None:
                logger.warning(
                    "kg.add_evidence called without learner_id; defaulting to __global__."
                )
            logger.info(
                "kg.add_evidence called for learner=%s node=%s success=%s",
                learner_key,
                node_id,
                success,
            )

            result = self._update_node_evidence(node_id, learner_key, success)

            logger.info(f"Evidence updated for node {node_id}")
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error in kg.add_evidence: {e}")
            raise KGServerError(f"Failed to update evidence for node {node_id}: {e}")

    def _query_frontier_nodes(self, learner_id: str, k: int) -> List[Dict[str, Any]]:
        """
        Query the actual knowledge graph database for frontier nodes.

        This method will be implemented when the KG schema is finalized.
        It should:
        1. Query nodes where all prerequisites are mastered
        2. Exclude nodes that are already mastered by this learner
        3. Calculate priority scores based on CEFR level, recency, and connections
        4. Return top k nodes
        """
        with sqlite3.connect(self.kg_db_path) as conn_kg, \
             sqlite3.connect(self.mastery_db_path) as conn_mastery:
            conn_kg.row_factory = sqlite3.Row
            conn_mastery.row_factory = sqlite3.Row
            cursor_kg = conn_kg.cursor()
            cursor_mastery = conn_mastery.cursor()

            # 1. Get all nodes and their direct prerequisites
            cursor_kg.execute(
                """
                SELECT
                    n.node_id,
                    n.type,
                    n.label,
                    n.cefr_level,
                    n.data_json,
                    GROUP_CONCAT(e.source_id) AS prerequisites
                FROM nodes n
                LEFT JOIN edges e ON n.node_id = e.target_id AND e.edge_type = 'prerequisite_of'
                GROUP BY n.node_id
                """
            )
            all_nodes_data = cursor_kg.fetchall()

            # 2. Get learner's mastery data from mastery.sqlite
            # Assuming mastery.sqlite has a table 'mastery' with 'node_id', 'learner_id', 'mastery_level'
            # For now, we'll use the 'evidence' table in kg.sqlite as a placeholder for mastery
            # In a real scenario, mastery.sqlite would be more complex (e.g., FSRS data)
            cursor_kg.execute(
                """
                SELECT node_id, success_count, error_count
                FROM evidence
                WHERE learner_id = ?
                """,
                (learner_id,),
            )
            learner_evidence = {row["node_id"]: row for row in cursor_kg.fetchall()}

            if learner_id != "__global__":
                cursor_kg.execute(
                    """
                    SELECT node_id, success_count, error_count
                    FROM evidence
                    WHERE learner_id = '__global__'
                    """,
                )
                for row in cursor_kg.fetchall():
                    learner_evidence.setdefault(row["node_id"], row)

            frontier_nodes: List[Dict[str, Any]] = []

            for node_row in all_nodes_data:
                node_id = node_row['node_id']
                prerequisites_str = node_row['prerequisites']
                prerequisites = prerequisites_str.split(',') if prerequisites_str else []

                # Check if all prerequisites are "mastered" (for now, just "seen" or "attempted successfully")
                prereqs_satisfied = True
                for prereq_id in prerequisites:
                    if prereq_id not in learner_evidence or learner_evidence[prereq_id]['success_count'] == 0:
                        prereqs_satisfied = False
                        break

                # Check if the node itself is already "mastered" by the learner
                # For simplicity, consider mastered if success_count > 0
                is_mastered = learner_evidence.get(node_id, {}).get('success_count', 0) > 0

                if prereqs_satisfied and not is_mastered:
                    node_data = json.loads(node_row['data_json'])
                    evidence = learner_evidence.get(node_id, {'success_count': 0, 'error_count': 0})
                    attempts = evidence['success_count'] + evidence['error_count']
                    mastery = evidence['success_count'] / attempts if attempts else 0.0

                    frontier_nodes.append(
                        {
                            "node_id": node_id,
                            "type": node_row['type'],
                            "label": node_row['label'],
                            "cefr_level": node_row['cefr_level'],
                            "prerequisites_satisfied": True,
                            "mastery_level": round(mastery, 2),
                            "can_do": node_data.get('can_do', []),
                            "priority_score": max(0.0, 1.0 - mastery), # Simple priority: less mastered = higher priority
                            "last_practiced": None # This would come from mastery.sqlite in full implementation
                        }
                    )
            
            # Sort by priority score (descending), then CEFR level, then label
            frontier_nodes.sort(key=lambda x: (x['priority_score'], x['cefr_level'], x['label']), reverse=True)

            return frontier_nodes[:k]

    def _query_node_prompt(self, node_id: str, kind: str) -> Dict[str, Any]:
        """
        Query the knowledge graph database for node prompt data.

        This method will be implemented when the KG schema is finalized.
        """
        with sqlite3.connect(self.kg_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    node_id,
                    cefr_level,
                    diagnostics,
                    prompts,
                    metadata,
                    data_json
                FROM nodes
                WHERE node_id = ?
            """,
                (node_id,),
            )

            row = cursor.fetchone()

        if not row:
            raise NodeNotFoundError(f"Node {node_id} not found")

        diagnostics = json.loads(row["diagnostics"]) if row["diagnostics"] else {}
        prompts = json.loads(row["prompts"]) if row["prompts"] else []
        metadata = json.loads(row["metadata"]) if row["metadata"] else {}
        data = json.loads(row["data_json"])

        instructions = data.get(
            "instructions",
            f"Practice the linguistic item: {row['node_id']}",
        )
        scaffolds = data.get("scaffolds", [])
        rubric_focus = data.get("rubric_focus", metadata.get("rubric_focus", []))
        target_forms = data.get("target_forms", diagnostics.get("form"))
        if isinstance(target_forms, str):
            target_forms = [target_forms]
        if not target_forms:
            target_forms = [row["node_id"]]

        return {
            "node_id": row["node_id"],
            "exercise_type": kind,
            "cefr_level": row["cefr_level"],
            "instructions": instructions,
            "scaffolds": scaffolds,
            "prompts": prompts or data.get("prompts", []),
            "target_forms": target_forms,
            "rubric_focus": rubric_focus,
        }

    def _update_node_evidence(self, node_id: str, learner_id: str, success: bool) -> Dict[str, Any]:
        """
        Update evidence counters in the knowledge graph database.

        This method will be implemented when the KG schema is finalized.
        """
        with sqlite3.connect(self.kg_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                "SELECT 1 FROM nodes WHERE node_id = ?",
                (node_id,),
            )
            if cursor.fetchone() is None:
                raise NodeNotFoundError(f"Node {node_id} not found")

            success_inc = 1 if success else 0
            error_inc = 0 if success else 1

            cursor.execute(
                """
                INSERT INTO evidence (node_id, learner_id, success_count, error_count, last_practiced)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(node_id, learner_id)
                DO UPDATE SET
                    success_count = success_count + ?,
                    error_count = error_count + ?,
                    last_practiced = CURRENT_TIMESTAMP
                """,
                (
                    node_id,
                    learner_id,
                    success_inc,
                    error_inc,
                    success_inc,
                    error_inc,
                ),
            )

            conn.commit()

            cursor.execute(
                """
                SELECT success_count, error_count, last_practiced
                FROM evidence
                WHERE node_id = ? AND learner_id = ?
                """,
                (node_id, learner_id),
            )
            row = cursor.fetchone()

        return {
            "node_id": node_id,
            "learner_id": learner_id,
            "success": success,
            "success_count": row["success_count"],
            "failure_count": row["error_count"],
            "last_practiced": row["last_practiced"],
            "total_attempts": row["success_count"] + row["error_count"],
            "mastery_estimate": (
                row["success_count"]
                / (row["success_count"] + row["error_count"])
                if (row["success_count"] + row["error_count"])
                else 0.0
            ),
        }

    def _update_mock_evidence(self, node_id: str, success: bool) -> Dict[str, Any]:
        """
        Mock implementation of evidence update for development.
        """
        # In mock mode, we just return simulated counts
        return {
            "node_id": node_id,
            "success": success,
            "success_count": 5 if success else 4,
            "failure_count": 1 if not success else 0,
            "total_attempts": 6 if success else 5,
            "mastery_estimate": 0.83 if success else 0.80
        }

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Returns MCP tool definitions for registration.

        This method provides metadata about the tools exposed by this server,
        which can be used by MCP clients to discover and invoke the tools.
        """
        return [
            {
                "name": "kg.next",
                "description": "Return frontier nodes (prerequisites satisfied, not yet mastered) for a learner",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "learner_id": {
                            "type": "string",
                            "description": "Unique identifier for the learner"
                        },
                        "k": {
                            "type": "integer",
                            "description": "Number of nodes to return (default: 5, max: 50)",
                            "default": 5,
                            "minimum": 1,
                            "maximum": 50
                        }
                    },
                    "required": ["learner_id"]
                }
            },
            {
                "name": "kg.prompt",
                "description": "Return exercise scaffold for a specific knowledge graph node",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "node_id": {
                            "type": "string",
                            "description": "Unique identifier for the knowledge graph node"
                        },
                        "kind": {
                            "type": "string",
                            "description": "Type of exercise (production, recognition, correction)",
                            "enum": ["production", "recognition", "correction"],
                            "default": "production"
                        }
                    },
                    "required": ["node_id"]
                }
            },
            {
                "name": "kg.add_evidence",
                "description": "Update evidence counter for a node based on learner performance",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "learner_id": {
                            "type": "string",
                            "description": "Unique identifier for the learner. Defaults to '__global__' if omitted.",
                        },
                        "node_id": {
                            "type": "string",
                            "description": "Unique identifier for the knowledge graph node"
                        },
                        "success": {
                            "type": "boolean",
                            "description": "Whether the learner's attempt was successful"
                        }
                    },
                    "required": ["node_id", "success"]
                }
            }
        ]
