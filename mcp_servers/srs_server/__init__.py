"""
SRS (Spaced Repetition System) MCP Server.

This package implements an MCP server for managing spaced repetition learning
using the FSRS (Free Spaced Repetition Scheduler) algorithm.

The server exposes tools for:
- Retrieving due items for review
- Updating FSRS parameters after reviews
- Getting learner statistics

Author: Spanish Learning Project
Version: 0.1.0
"""

__version__ = "0.1.0"
__author__ = "Spanish Learning Project"

from .server import SRSServer

__all__ = ["SRSServer"]
