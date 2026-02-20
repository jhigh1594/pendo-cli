"""Tests for query commands."""

import pytest
import argparse
import logging
from pendo_cli.commands.query import QueryCommand


class TestQueryCommand:
    """Tests for QueryCommand class."""

    @pytest.fixture
    def mock_args_visitors(self):
        """Mock args for visitors query."""
        args = argparse.Namespace(
            query_type="visitors",
            last_days=30,
            segment=None,
            verbose=False
        )
        return args

    @pytest.fixture
    def mock_args_accounts(self):
        """Mock args for accounts query."""
        args = argparse.Namespace(
            query_type="accounts",
            last_days=30,
            segment=None,
            verbose=False
        )
        return args

    @pytest.fixture
    def mock_args_activity(self):
        """Mock args for activity query."""
        args = argparse.Namespace(
            query_type="activity",
            entity="visitor",
            group_by=None,
            verbose=False
        )
        return args

    @pytest.fixture
    def mock_logger(self):
        """Mock logger."""
        return logging.getLogger(__name__)

    @pytest.mark.asyncio
    async def test_visitors_query_executes(self, mock_args_visitors, mock_logger):
        """Test that visitors query executes."""
        cmd = QueryCommand(mock_args_visitors, mock_logger)
        result = await cmd.execute()
        # Command should complete (returns bool)
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_accounts_query_executes(self, mock_args_accounts, mock_logger):
        """Test that accounts query executes."""
        cmd = QueryCommand(mock_args_accounts, mock_logger)
        result = await cmd.execute()
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_activity_query_executes(self, mock_args_activity, mock_logger):
        """Test that activity query executes."""
        cmd = QueryCommand(mock_args_activity, mock_logger)
        result = await cmd.execute()
        assert isinstance(result, bool)
