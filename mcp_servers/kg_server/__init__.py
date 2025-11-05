"""
Knowledge Graph MCP Server

Exposes knowledge graph operations for the Spanish language learning system.
Provides tools for querying learnable nodes, generating exercise prompts, and
tracking learner evidence.
"""

from mcp_servers.kg_server.server import KGServer

__version__ = "0.1.0"
__all__ = ["KGServer"]
