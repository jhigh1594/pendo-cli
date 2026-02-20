"""Base command class for CLI commands."""

from abc import ABC, abstractmethod
import logging
from typing import Any


class BaseCommand(ABC):
    """Abstract base class for CLI commands.

    All commands must inherit from this class and implement the execute method.
    """

    def __init__(self, args: Any, logger: logging.Logger):
        """Initialize the command.

        Args:
            args: Parsed command-line arguments
            logger: Logger instance for output
        """
        self.args = args
        self.logger = logger

    @abstractmethod
    async def execute(self) -> bool:
        """Execute the command.

        Returns:
            True on success, False on failure
        """
        pass
