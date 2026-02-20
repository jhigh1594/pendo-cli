"""Base collector for data collection workflows."""

from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, Optional


class BaseCollector(ABC):
    """Abstract base class for data collectors.

    Collectors are responsible for gathering data from external sources
    (like the Pendo API) in a structured way.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the collector.

        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def collect(self, **kwargs: Any) -> Dict[str, Any]:
        """Collect data from the source.

        Args:
            **kwargs: Additional parameters for collection

        Returns:
            Dictionary with collected data and any errors
        """
        pass
