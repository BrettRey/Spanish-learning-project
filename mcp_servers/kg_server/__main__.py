"""
Knowledge Graph MCP Server CLI Entry Point

Provides a command-line interface for running the KG MCP server.
Supports both standalone mode (for testing) and MCP server mode.

Usage:
    python -m mcp_servers.kg_server --help
    python -m mcp_servers.kg_server --test
    python -m mcp_servers.kg_server --mode server
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional

from mcp_servers.kg_server.server import KGServer, KGServerError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_test_mode(server: KGServer) -> int:
    """
    Run server in test mode, demonstrating all three tools.

    Args:
        server: Initialized KGServer instance

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        print("\n" + "=" * 70)
        print("Knowledge Graph MCP Server - Test Mode")
        print("=" * 70)

        # Test 1: kg.next
        print("\n1. Testing kg.next (frontier nodes)")
        print("-" * 70)
        result = server.kg_next(learner_id="test_learner", k=3)
        print(result)

        # Test 2: kg.prompt
        print("\n2. Testing kg.prompt (exercise scaffold)")
        print("-" * 70)
        result = server.kg_prompt(
            node_id="constr.es.subjunctive_present",
            kind="production"
        )
        print(result)

        # Test 3: kg.add_evidence (success)
        print("\n3. Testing kg.add_evidence (success=True)")
        print("-" * 70)
        result = server.kg_add_evidence(
            node_id="constr.es.subjunctive_present",
            success=True
        )
        print(result)

        # Test 4: kg.add_evidence (failure)
        print("\n4. Testing kg.add_evidence (success=False)")
        print("-" * 70)
        result = server.kg_add_evidence(
            node_id="lexeme.es.ojalá",
            success=False
        )
        print(result)

        # Test 5: Tool definitions
        print("\n5. MCP Tool Definitions")
        print("-" * 70)
        tools = server.get_tool_definitions()
        print(json.dumps(tools, indent=2))

        print("\n" + "=" * 70)
        print("All tests completed successfully!")
        print("=" * 70 + "\n")

        return 0

    except Exception as e:
        logger.error(f"Test mode failed: {e}")
        print(f"\nError: {e}", file=sys.stderr)
        return 1


def run_server_mode(
    server: KGServer,
    host: str = "localhost",
    port: int = 8000
) -> int:
    """
    Run server in MCP server mode.

    This is a placeholder for the actual MCP server implementation.
    In a full implementation, this would start an HTTP/JSON-RPC server
    that exposes the KG tools according to the MCP protocol.

    Args:
        server: Initialized KGServer instance
        host: Server host address
        port: Server port number

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print(f"\nStarting KG MCP Server at {host}:{port}")
    print("Note: Full MCP server mode not yet implemented.")
    print("This is a placeholder for future MCP protocol integration.\n")

    print("Tools available:")
    for tool in server.get_tool_definitions():
        print(f"  - {tool['name']}: {tool['description']}")

    print("\nFor now, use --test mode to try the tools.")
    return 0


def run_interactive_mode(server: KGServer) -> int:
    """
    Run server in interactive mode for manual testing.

    Args:
        server: Initialized KGServer instance

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print("\n" + "=" * 70)
    print("Knowledge Graph MCP Server - Interactive Mode")
    print("=" * 70)
    print("\nAvailable commands:")
    print("  next <learner_id> [k]         - Get frontier nodes")
    print("  prompt <node_id> [kind]       - Get exercise prompt")
    print("  evidence <node_id> <success>  - Add evidence (success: true/false)")
    print("  tools                         - List tool definitions")
    print("  quit                          - Exit interactive mode")
    print()

    while True:
        try:
            user_input = input("kg> ").strip()

            if not user_input:
                continue

            parts = user_input.split()
            command = parts[0].lower()

            if command == "quit":
                print("Exiting interactive mode.")
                return 0

            elif command == "next":
                if len(parts) < 2:
                    print("Usage: next <learner_id> [k]")
                    continue
                learner_id = parts[1]
                k = int(parts[2]) if len(parts) > 2 else 5
                result = server.kg_next(learner_id, k)
                print(result)

            elif command == "prompt":
                if len(parts) < 2:
                    print("Usage: prompt <node_id> [kind]")
                    continue
                node_id = parts[1]
                kind = parts[2] if len(parts) > 2 else "production"
                result = server.kg_prompt(node_id, kind)
                print(result)

            elif command == "evidence":
                if len(parts) < 3:
                    print("Usage: evidence <node_id> <success>")
                    continue
                node_id = parts[1]
                success = parts[2].lower() in ["true", "1", "yes", "t", "y"]
                result = server.kg_add_evidence(node_id, success)
                print(result)

            elif command == "tools":
                tools = server.get_tool_definitions()
                print(json.dumps(tools, indent=2))

            else:
                print(f"Unknown command: {command}")
                print("Type 'quit' to exit or try: next, prompt, evidence, tools")

        except KeyboardInterrupt:
            print("\nExiting interactive mode.")
            return 0
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)


def main() -> int:
    """
    Main entry point for the KG MCP server.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(
        description="Knowledge Graph MCP Server for Spanish Language Learning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run in test mode with mock data
  python -m mcp_servers.kg_server --test

  # Run in interactive mode
  python -m mcp_servers.kg_server --interactive

  # Run as MCP server (placeholder)
  python -m mcp_servers.kg_server --mode server

  # Use real database (when available)
  python -m mcp_servers.kg_server --test --no-mock --kg-db ../kg/kg.sqlite

For more information, see mcp_servers/kg_server/README.md
        """
    )

    parser.add_argument(
        "--mode",
        choices=["test", "server", "interactive"],
        default="test",
        help="Server operation mode (default: test)"
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode (shortcut for --mode test)"
    )

    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode (shortcut for --mode interactive)"
    )

    parser.add_argument(
        "--no-mock",
        action="store_true",
        help="Use real databases instead of mock data"
    )

    parser.add_argument(
        "--kg-db",
        type=Path,
        help="Path to knowledge graph SQLite database"
    )

    parser.add_argument(
        "--mastery-db",
        type=Path,
        help="Path to learner mastery SQLite database"
    )

    parser.add_argument(
        "--host",
        default="localhost",
        help="Server host address (default: localhost)"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Server port number (default: 8000)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )

    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Determine mode
    mode = args.mode
    if args.test:
        mode = "test"
    elif args.interactive:
        mode = "interactive"

    # Initialize server
    try:
        use_mock = not args.no_mock
        server = KGServer(
            kg_db_path=args.kg_db,
            mastery_db_path=args.mastery_db,
            use_mock_data=use_mock
        )

        if use_mock:
            logger.info("Server initialized with mock data")
        else:
            logger.info("Server initialized with real databases")

    except Exception as e:
        logger.error(f"Failed to initialize server: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Run in selected mode
    if mode == "test":
        return run_test_mode(server)
    elif mode == "interactive":
        return run_interactive_mode(server)
    elif mode == "server":
        return run_server_mode(server, args.host, args.port)
    else:
        logger.error(f"Unknown mode: {mode}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
