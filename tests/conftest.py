"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def sample_subscription_id():
    """Sample subscription ID for testing."""
    return "4598576627318784"


@pytest.fixture
def sample_app_id():
    """Sample app ID for testing."""
    return "-323232"


@pytest.fixture
def mock_pendo_config(sample_subscription_id, sample_app_id):
    """Mock PendoConfig for testing."""
    from pendo_cli.api.models import PendoConfig

    return PendoConfig(
        subscription_id=sample_subscription_id,
        app_id=sample_app_id
    )
