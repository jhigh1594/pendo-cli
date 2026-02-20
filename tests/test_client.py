"""Tests for Pendo API client."""

import pytest
from pendo_cli.api.client import PendoClient
from pendo_cli.api.models import PendoConfig


class TestPendoConfig:
    """Tests for PendoConfig dataclass."""

    def test_config_initialization(self):
        """Test that PendoConfig can be initialized with required fields."""
        config = PendoConfig(
            subscription_id="4598576627318784",
            app_id="-323232"
        )
        assert config.subscription_id == "4598576627318784"
        assert config.app_id == "-323232"
        assert config.base_url == "https://app.pendo.io"  # default
        assert config.timeout == 30  # default
        assert config.max_retries == 3  # default

    def test_config_with_custom_defaults(self):
        """Test that PendoConfig accepts custom default values."""
        config = PendoConfig(
            subscription_id="123",
            app_id="-456",
            base_url="https://custom.pendo.io",
            timeout=60,
            max_retries=5
        )
        assert config.base_url == "https://custom.pendo.io"
        assert config.timeout == 60
        assert config.max_retries == 5


class TestPendoClient:
    """Tests for PendoClient class."""

    def test_client_initialization(self):
        """Test that PendoClient can be initialized with config."""
        config = PendoConfig(
            subscription_id="4598576627318784",
            app_id="-323232"
        )
        client = PendoClient(config)
        assert client.subscription_id == "4598576627318784"
        assert client.config.subscription_id == "4598576627318784"

    @pytest.mark.asyncio
    async def test_list_segments_returns_expected_structure(self):
        """Test that list_segments returns dict with data and errors keys."""
        config = PendoConfig(
            subscription_id="4598576627318784",
            app_id="-323232"
        )
        client = PendoClient(config)

        # This test will fail because PendoClient doesn't exist yet
        # and list_segments method doesn't exist
        result = await client.list_segments()

        # Verify the expected structure
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "data" in result, "Result should have 'data' key"
        assert "errors" in result, "Result should have 'errors' key"
        assert isinstance(result["errors"], list), "Errors should be a list"

    @pytest.mark.asyncio
    async def test_create_segment_returns_expected_structure(self):
        """Test that create_segment returns dict with data and errors keys."""
        config = PendoConfig(
            subscription_id="4598576627318784",
            app_id="-323232"
        )
        client = PendoClient(config)

        segment_data = {
            "name": "Test Segment",
            "description": "Test description"
        }
        result = await client.create_segment(segment_data)

        # Verify the expected structure
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "data" in result, "Result should have 'data' key"
        assert "errors" in result, "Result should have 'errors' key"
        assert isinstance(result["errors"], list), "Errors should be a list"

    @pytest.mark.asyncio
    async def test_update_segment_returns_expected_structure(self):
        """Test that update_segment returns dict with data and errors keys."""
        config = PendoConfig(
            subscription_id="4598576627318784",
            app_id="-323232"
        )
        client = PendoClient(config)

        segment_data = {"name": "Updated Segment"}
        result = await client.update_segment("segment123", segment_data)

        # Verify the expected structure
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "data" in result, "Result should have 'data' key"
        assert "errors" in result, "Result should have 'errors' key"
        assert isinstance(result["errors"], list), "Errors should be a list"

    @pytest.mark.asyncio
    async def test_delete_segment_returns_expected_structure(self):
        """Test that delete_segment returns dict with data and errors keys."""
        config = PendoConfig(
            subscription_id="4598576627318784",
            app_id="-323232"
        )
        client = PendoClient(config)

        result = await client.delete_segment("segment123")

        # Verify the expected structure
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "data" in result, "Result should have 'data' key"
        assert "errors" in result, "Result should have 'errors' key"
        assert isinstance(result["errors"], list), "Errors should be a list"
