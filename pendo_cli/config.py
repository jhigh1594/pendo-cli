"""Configuration management for Pendo CLI."""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

from dotenv import load_dotenv


@dataclass
class Config:
    """Configuration for Pendo CLI.

    Configuration is loaded from environment variables with
    optional defaults. The priority order is:
    1. Environment variables
    2. .env file (if present)
    3. Built-in defaults
    """

    subscription_id: str = field(
        default_factory=lambda: os.getenv("PENDO_SUBSCRIPTION_ID", "4598576627318784")
    )
    app_id: str = field(default_factory=lambda: os.getenv("PENDO_APP_ID", "-323232"))
    base_url: str = field(
        default_factory=lambda: os.getenv("PENDO_BASE_URL", "https://app.pendo.io")
    )
    api_key: Optional[str] = field(default_factory=lambda: os.getenv("PENDO_API_KEY"))
    timeout: int = field(default=30)
    max_retries: int = field(default=3)

    @classmethod
    def load(cls, env_file: Optional[Path] = None) -> "Config":
        """Load configuration from environment.

        Args:
            env_file: Optional path to .env file

        Returns:
            Config instance
        """
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()

        return cls()

    def to_dict(self) -> dict:
        """Convert config to dictionary.

        Returns:
            Dictionary representation of config
        """
        return {
            "subscription_id": self.subscription_id,
            "app_id": self.app_id,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
        }
