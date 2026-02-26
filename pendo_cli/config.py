"""Configuration management for Pendo CLI."""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

from dotenv import load_dotenv

from pendo_cli.api.models import PendoConfig

# Supported subscription names for multi-subscription support
SUBSCRIPTION_NAMES = ("default", "roadmaps", "portfolios")


def get_config(subscription: Optional[str] = None, env_file: Optional[Path] = None) -> PendoConfig:
    """Load PendoConfig for the given subscription.

    Args:
        subscription: Name of subscription ("default", "roadmaps", or "portfolios").
            If None, uses PENDO_SUBSCRIPTION env var (default "default").
        env_file: Optional path to .env file.

    Returns:
        PendoConfig for the selected subscription.

    Raises:
        ValueError: If subscription name is not supported.
    """
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()

    name = (subscription or os.getenv("PENDO_SUBSCRIPTION", "default")).strip().lower()
    if name not in SUBSCRIPTION_NAMES:
        raise ValueError(
            f"Unknown subscription {name!r}. Use one of: {', '.join(SUBSCRIPTION_NAMES)}"
        )

    base_url = os.getenv("PENDO_BASE_URL", "https://app.pendo.io")
    timeout = int(os.getenv("PENDO_TIMEOUT", "30"))
    max_retries = int(os.getenv("PENDO_MAX_RETRIES", "3"))

    if name == "default":
        subscription_id = os.getenv("PENDO_SUBSCRIPTION_ID", "4598576627318784")
        app_id = os.getenv("PENDO_APP_ID", "-323232")
        api_key = os.getenv("PENDO_API_KEY")
    elif name == "roadmaps":
        subscription_id = os.getenv(
            "PENDO_ROADMAPS_SUBSCRIPTION_ID", "6602363610660864"
        )
        app_id = os.getenv("PENDO_ROADMAPS_APP_ID", "5553517598146560")
        api_key = os.getenv("PENDO_ROADMAPS_API_KEY")
    else:
        # portfolios
        subscription_id = os.getenv(
            "PENDO_PORTFOLIOS_SUBSCRIPTION_ID", "5878812817883136"
        )
        app_id = os.getenv("PENDO_PORTFOLIOS_APP_ID", "-323232")
        api_key = os.getenv("PENDO_PORTFOLIOS_API_KEY")

    return PendoConfig(
        subscription_id=subscription_id,
        app_id=app_id,
        base_url=base_url,
        timeout=timeout,
        max_retries=max_retries,
        api_key=api_key,
    )


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
