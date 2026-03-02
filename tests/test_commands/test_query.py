"""Tests for query commands."""

import argparse
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pendo_cli.commands.query import QueryCommand, _format_output, _time_series_for_date_range


class TestQueryCommand:
    """Tests for QueryCommand class."""

    @pytest.fixture
    def mock_args_visitors(self):
        """Mock args for visitors query."""
        return argparse.Namespace(
            query_type="visitors",
            format="table",
            subscription="default",
            from_date=None,
            to_date=None,
            last_days=None,
            new_last_days=None,
            inactive_days=None,
            verbose=False,
        )

    @pytest.fixture
    def mock_args_accounts(self):
        """Mock args for accounts query."""
        return argparse.Namespace(
            query_type="accounts",
            format="table",
            subscription="default",
            from_date=None,
            to_date=None,
            last_days=None,
            new_last_days=None,
            verbose=False,
        )

    @pytest.fixture
    def mock_args_activity(self):
        """Mock args for activity query."""
        return argparse.Namespace(
            query_type="activity",
            entity="visitor",
            group_by=None,
            verbose=False,
        )

    @pytest.fixture
    def mock_args_usage(self):
        """Mock args for usage query."""
        return argparse.Namespace(
            query_type="usage",
            mode="wau",
            group_by="none",
            format="table",
            subscription="default",
            from_date=None,
            to_date=None,
            last_days=None,
            verbose=False,
        )

    @pytest.fixture
    def mock_args_features(self):
        """Mock args for features query."""
        return argparse.Namespace(
            query_type="features",
            top=10,
            feature_id=None,
            format="table",
            subscription="default",
            from_date=None,
            to_date=None,
            last_days=30,
            verbose=False,
        )

    @pytest.fixture
    def mock_args_pages(self):
        """Mock args for pages query."""
        return argparse.Namespace(
            query_type="pages",
            top=10,
            page_id=None,
            format="table",
            subscription="default",
            from_date=None,
            to_date=None,
            last_days=30,
            verbose=False,
        )

    @pytest.fixture
    def mock_logger(self):
        """Mock logger."""
        return logging.getLogger(__name__)

    def _make_mock_client(self, data: dict):
        """Create a mock PendoClient that returns given data from post_aggregation."""
        client = MagicMock()
        client.post_aggregation = AsyncMock(return_value={"data": data, "errors": []})
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=None)
        return client

    @pytest.mark.asyncio
    @patch("pendo_cli.commands.query.PendoClient")
    @patch("pendo_cli.commands.query.get_config")
    async def test_visitors_query_executes(
        self, mock_get_config, mock_client_cls, mock_args_visitors, mock_logger
    ):
        """Test that visitors query executes with mocked API."""
        mock_client_cls.return_value = self._make_mock_client(
            {"results": [{"visitorId": "v1", "accountId": "a1", "firstvisit": 123}]}
        )
        mock_get_config.return_value = MagicMock()
        cmd = QueryCommand(mock_args_visitors, mock_logger)
        result = await cmd.execute()
        assert result is True

    @pytest.mark.asyncio
    @patch("pendo_cli.commands.query.PendoClient")
    @patch("pendo_cli.commands.query.get_config")
    async def test_accounts_query_executes(
        self, mock_get_config, mock_client_cls, mock_args_accounts, mock_logger
    ):
        """Test that accounts query executes with mocked API."""
        mock_client_cls.return_value = self._make_mock_client(
            {"results": [{"accountId": "a1", "name": "Acme", "planlevel": "Pro"}]}
        )
        mock_get_config.return_value = MagicMock()
        cmd = QueryCommand(mock_args_accounts, mock_logger)
        result = await cmd.execute()
        assert result is True

    @pytest.mark.asyncio
    async def test_activity_query_executes(self, mock_args_activity, mock_logger):
        """Test that activity query executes."""
        cmd = QueryCommand(mock_args_activity, mock_logger)
        result = await cmd.execute()
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    @patch("pendo_cli.commands.query.PendoClient")
    @patch("pendo_cli.commands.query.get_config")
    async def test_usage_query_executes(
        self, mock_get_config, mock_client_cls, mock_args_usage, mock_logger
    ):
        """Test that usage query executes with mocked API."""
        mock_client_cls.return_value = self._make_mock_client(
            {"results": [{"activeUsers": 42}]}
        )
        mock_get_config.return_value = MagicMock()
        cmd = QueryCommand(mock_args_usage, mock_logger)
        result = await cmd.execute()
        assert result is True

    @pytest.mark.asyncio
    @patch("pendo_cli.commands.query.PendoClient")
    @patch("pendo_cli.commands.query.get_config")
    async def test_features_query_executes(
        self, mock_get_config, mock_client_cls, mock_args_features, mock_logger
    ):
        """Test that features query executes with mocked API."""
        mock_client_cls.return_value = self._make_mock_client(
            {
                "results": [
                    {
                        "featureId": "f1",
                        "totalEvents": 100,
                        "totalMinutes": 50,
                        "uniqueVisitors": 25,
                    }
                ]
            }
        )
        mock_get_config.return_value = MagicMock()
        cmd = QueryCommand(mock_args_features, mock_logger)
        result = await cmd.execute()
        assert result is True

    @pytest.mark.asyncio
    @patch("pendo_cli.commands.query.PendoClient")
    @patch("pendo_cli.commands.query.get_config")
    async def test_pages_query_executes(
        self, mock_get_config, mock_client_cls, mock_args_pages, mock_logger
    ):
        """Test that pages query executes with mocked API."""
        mock_client_cls.return_value = self._make_mock_client(
            {
                "results": [
                    {
                        "pageId": "p1",
                        "totalEvents": 80,
                        "totalMinutes": 40,
                        "uniqueVisitors": 20,
                    }
                ]
            }
        )
        mock_get_config.return_value = MagicMock()
        cmd = QueryCommand(mock_args_pages, mock_logger)
        result = await cmd.execute()
        assert result is True


class TestFormatOutput:
    """Tests for _format_output helper."""

    def test_format_table(self):
        """Table format produces aligned columns."""
        results = [{"a": 1, "b": 2}, {"a": 10, "b": 20}]
        out = _format_output(results, "table")
        assert "a" in out and "b" in out
        assert "1" in out and "10" in out

    def test_format_json(self):
        """JSON format produces valid JSON."""
        results = [{"wau": 42}]
        out = _format_output(results, "json")
        assert '"wau": 42' in out or '"wau":42' in out

    def test_format_csv(self):
        """CSV format produces header and rows."""
        results = [{"x": 1, "y": 2}]
        out = _format_output(results, "csv")
        assert "x" in out and "y" in out
        assert "1" in out and "2" in out


class TestTimeSeriesForDateRange:
    """Tests for _time_series_for_date_range helper."""

    def test_relative_fallback(self):
        """No dates yields relative window."""
        ts, label = _time_series_for_date_range(None, None, default_last_days=7)
        assert ts["first"] == "now()"
        assert ts["count"] == -7
        assert "last 7 days" in label

    def test_absolute_range(self):
        """Valid from_date and to_date yield epoch ms."""
        ts, label = _time_series_for_date_range("2025-01-01", "2025-01-07", default_last_days=7)
        assert isinstance(ts["first"], int)
        assert ts["count"] == 6  # Jan 1 to Jan 7 inclusive is 7 days, end - start = 6
        assert "2025-01-01" in label
