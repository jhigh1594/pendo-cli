"""Entry point for python -m pendo_cli."""

import asyncio
import sys

from pendo_cli.cli import main


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
