#!/usr/bin/env python3
"""Pendo CLI - Pendo API automation command-line interface.

Usage:
    pendo segment list
    pendo segment create --name "Power Users"
    pendo query visitors --last-days 30
    pendo export segments --format json --output segments.json
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

from pendo_cli.commands.segment import SegmentCommand
from pendo_cli.commands.query import QueryCommand


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Set up logging configuration.

    Args:
        verbose: Enable debug-level logging

    Returns:
        Configured logger instance
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Pendo API automation CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--subscription",
        choices=["default", "roadmaps"],
        default=None,
        help="Pendo subscription to use (default: PENDO_SUBSCRIPTION env or 'default')",
    )

    # Add subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Segment commands
    segment_parser = subparsers.add_parser("segment", help="Segment management")
    segment_subparsers = segment_parser.add_subparsers(dest="segment_action")

    # segment list
    segment_subparsers.add_parser("list", help="List all segments")

    # segment create
    segment_create_parser = segment_subparsers.add_parser(
        "create", help="Create a new segment"
    )
    segment_create_parser.add_argument("--name", required=True, help="Segment name")
    segment_create_parser.add_argument(
        "--description", default="", help="Segment description"
    )

    # segment update
    segment_update_parser = segment_subparsers.add_parser(
        "update", help="Update an existing segment"
    )
    segment_update_parser.add_argument("segment_id", help="Segment ID to update")
    segment_update_parser.add_argument("--name", help="New segment name")
    segment_update_parser.add_argument("--description", help="New segment description")

    # segment delete
    segment_delete_parser = segment_subparsers.add_parser(
        "delete", help="Delete a segment"
    )
    segment_delete_parser.add_argument("segment_id", help="Segment ID to delete")

    # Query commands
    query_parser = subparsers.add_parser("query", help="Query data")
    query_subparsers = query_parser.add_subparsers(dest="query_type")
    query_subparsers.add_parser("visitors", help="Query visitors")
    query_subparsers.add_parser("accounts", help="Query accounts")
    query_subparsers.add_parser("activity", help="Query activity")
    wau_parser = query_subparsers.add_parser(
        "wau", help="Weekly (or N-day) active users: unique visitors with activity in window"
    )
    wau_parser.add_argument(
        "--last-days",
        type=int,
        default=7,
        metavar="N",
        help="Count unique visitors active in the last N days (default: 7)",
    )
    events_parser = query_subparsers.add_parser(
        "events", help="Query track event counts (e.g. cards created)"
    )
    events_parser.add_argument(
        "--event-name",
        default="core-card-service POST /io/card",
        help="Track event name (default: core-card-service POST /io/card)",
    )
    events_parser.add_argument(
        "--from-date",
        default="2025-01-01",
        help="Start date YYYY-MM-DD (default: 2025-01-01)",
    )
    events_parser.add_argument(
        "--to-date",
        default="2025-12-31",
        help="End date YYYY-MM-DD (default: 2025-12-31)",
    )
    events_parser.add_argument(
        "--country",
        default="US",
        help="Filter by visitor country code, e.g. US (default: US)",
    )

    # Export commands (placeholder for future implementation)
    export_parser = subparsers.add_parser("export", help="Export data")
    export_parser.add_argument("--format", choices=["json", "csv"], default="json")
    export_parser.add_argument("--output", type=str, required=True)

    return parser.parse_args()


async def main() -> int:
    """Main CLI entry point.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    args = parse_args()
    logger = setup_logging(args.verbose)

    if not args.command:
        logger.error("No command specified. Use --help for usage information.")
        return 1

    # Route to appropriate command handler
    if args.command == "segment":
        cmd = SegmentCommand(args, logger)
        result = await cmd.execute()
        return 0 if result else 1
    elif args.command == "query":
        cmd = QueryCommand(args, logger)
        result = await cmd.execute()
        return 0 if result else 1
    elif args.command == "export":
        logger.error("Export commands not yet implemented")
        return 1
    else:
        logger.error(f"Unknown command: {args.command}")
        return 1


def entry_point() -> int:
    """Synchronous entry point for console_scripts.

    Returns:
        Exit code
    """
    try:
        return asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 130
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(entry_point())
