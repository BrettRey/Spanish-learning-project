"""
SRS MCP Server Entry Point.

This module provides the command-line interface for running the SRS MCP server.
It supports both standalone mode (for testing) and MCP protocol mode.

Usage:
    python -m mcp_servers.srs_server --help
    python -m mcp_servers.srs_server --test
    python -m mcp_servers.srs_server --db path/to/mastery.sqlite
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from .server import SRSServer, register_tools


def create_parser() -> argparse.ArgumentParser:
    """
    Create argument parser for CLI.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog="srs_server",
        description="SRS (Spaced Repetition System) MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run in test mode with mock data
  python -m mcp_servers.srs_server --test

  # Run with specific database
  python -m mcp_servers.srs_server --db ../state/mastery.sqlite

  # Show tool definitions
  python -m mcp_servers.srs_server --show-tools

  # Run interactive demo
  python -m mcp_servers.srs_server --demo

For integration with MCP clients, see README.md
        """
    )

    parser.add_argument(
        "--db",
        type=str,
        help="Path to mastery.sqlite database (uses mock data if not specified)",
        metavar="PATH"
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode with sample queries"
    )

    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run interactive demo mode"
    )

    parser.add_argument(
        "--show-tools",
        action="store_true",
        help="Display available MCP tools and exit"
    )

    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version and exit"
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level (default: INFO)"
    )

    return parser


def show_tools(server: SRSServer) -> None:
    """
    Display available MCP tools and their signatures.

    Args:
        server: SRSServer instance
    """
    tools = register_tools(server)

    print("\n" + "=" * 70)
    print("SRS MCP SERVER - AVAILABLE TOOLS")
    print("=" * 70 + "\n")

    for tool_name, tool_def in tools.items():
        print(f"Tool: {tool_name}")
        print(f"Description: {tool_def['description']}")
        print("Parameters:")

        for param_name, param_def in tool_def['parameters'].items():
            required = " (required)" if param_def['required'] else " (optional)"
            default = f" [default: {param_def.get('default')}]" if 'default' in param_def else ""
            print(f"  - {param_name}: {param_def['type']}{required}{default}")
            print(f"    {param_def['description']}")

        print()


def run_test_mode(server: SRSServer) -> None:
    """
    Run server in test mode with sample queries.

    Args:
        server: SRSServer instance
    """
    print("\n" + "=" * 70)
    print("SRS MCP SERVER - TEST MODE")
    print("=" * 70 + "\n")

    print("Test 1: Get due items for learner 'brett'")
    print("-" * 70)
    result = server.get_due_items("brett", limit=5)
    print(result)
    print()

    print("Test 2: Update item with quality=4 (easy)")
    print("-" * 70)
    result = server.update_item("card.es.ser_vs_estar.001", quality=4)
    print(result)
    print()

    print("Test 3: Get learner statistics")
    print("-" * 70)
    result = server.get_stats("brett")
    print(result)
    print()

    print("Test 4: Error handling - invalid learner_id")
    print("-" * 70)
    result = server.get_due_items("", limit=5)
    print(result)
    print()

    print("Test 5: Error handling - invalid quality score")
    print("-" * 70)
    result = server.update_item("card.es.test.001", quality=10)
    print(result)
    print()

    print("=" * 70)
    print("All tests completed successfully!")
    print("=" * 70 + "\n")


def run_demo_mode(server: SRSServer) -> None:
    """
    Run interactive demo mode.

    Args:
        server: SRSServer instance
    """
    print("\n" + "=" * 70)
    print("SRS MCP SERVER - INTERACTIVE DEMO")
    print("=" * 70 + "\n")

    learner_id = input("Enter learner ID (default: brett): ").strip() or "brett"

    while True:
        print("\nAvailable commands:")
        print("  1. Get due items")
        print("  2. Update an item")
        print("  3. Get statistics")
        print("  4. Exit")

        choice = input("\nEnter choice (1-4): ").strip()

        if choice == "1":
            limit = input("Number of items (default: 10): ").strip()
            limit = int(limit) if limit else 10
            result = server.get_due_items(learner_id, limit)
            print("\nResult:")
            print(result)

        elif choice == "2":
            item_id = input("Enter item ID: ").strip()
            quality = input("Enter quality (0-5): ").strip()
            try:
                quality = int(quality)
                result = server.update_item(item_id, quality)
                print("\nResult:")
                print(result)
            except ValueError:
                print("Error: Quality must be an integer")

        elif choice == "3":
            result = server.get_stats(learner_id)
            print("\nResult:")
            print(result)

        elif choice == "4":
            print("\nExiting demo mode...")
            break

        else:
            print("Invalid choice. Please enter 1-4.")


def main(argv: Optional[list] = None) -> int:
    """
    Main entry point for the SRS MCP server.

    Args:
        argv: Command line arguments (uses sys.argv if None)

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    # Show version
    if args.version:
        from . import __version__
        print(f"SRS MCP Server version {__version__}")
        return 0

    # Configure logging
    import logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Initialize server
    db_path = args.db if args.db else None
    if db_path:
        db_file = Path(db_path)
        if not db_file.exists():
            print(f"Warning: Database file not found: {db_path}", file=sys.stderr)
            print("Continuing with mock data...", file=sys.stderr)
            db_path = None

    server = SRSServer(db_path=db_path)

    # Show tools
    if args.show_tools:
        show_tools(server)
        return 0

    # Test mode
    if args.test:
        run_test_mode(server)
        return 0

    # Demo mode
    if args.demo:
        try:
            run_demo_mode(server)
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
        return 0

    # Default: show help if no mode specified
    if not any([args.test, args.demo, args.show_tools]):
        print("No operation specified. Use --help for usage information.\n")
        print("Quick start:")
        print("  --test       Run test mode")
        print("  --demo       Run interactive demo")
        print("  --show-tools List available MCP tools")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
