"""Query commands for Pendo data."""

from datetime import datetime, timezone
from typing import Any
import logging

from pendo_cli.commands.base import BaseCommand
from pendo_cli.api.client import PendoClient, PendoConfig


logger = logging.getLogger(__name__)


class QueryCommand(BaseCommand):
    """Handle query commands for Pendo data.

    Supports: visitors, accounts, activity
    """

    async def execute(self) -> bool:
        """Execute the query command.

        Returns:
            True on success, False on failure
        """
        from pendo_cli.config import get_config

        subscription = getattr(self.args, "subscription", None)
        config = get_config(subscription)

        query_type = getattr(self.args, "query_type", None)

        # Use async context manager to properly close the session
        async with PendoClient(config) as client:
            if query_type == "visitors":
                return await self._query_visitors(client)
            elif query_type == "accounts":
                return await self._query_accounts(client)
            elif query_type == "activity":
                return await self._query_activity(client)
            elif query_type == "wau":
                return await self._query_wau(client)
            elif query_type == "events":
                return await self._query_events(client)
            else:
                self.logger.error(f"Unknown query type: {query_type}")
                return False

    async def _query_visitors(self, client: PendoClient) -> bool:
        """Query visitors.

        Args:
            client: Pendo API client

        Returns:
            True on success, False on failure
        """
        last_days = getattr(self.args, "last_days", 30)
        segment = getattr(self.args, "segment", None)

        self.logger.info(f"Querying visitors from last {last_days} days...")

        # This would use the Pendo MCP aggregation query
        # For now, we just log the query parameters
        if segment:
            self.logger.info(f"Filtering by segment: {segment}")

        # TODO: Implement actual query via Pendo API
        self.logger.warning("Visitor query not yet fully implemented")
        return True

    async def _query_accounts(self, client: PendoClient) -> bool:
        """Query accounts.

        Args:
            client: Pendo API client

        Returns:
            True on success, False on failure
        """
        last_days = getattr(self.args, "last_days", 30)

        self.logger.info(f"Querying accounts from last {last_days} days...")

        # TODO: Implement actual query via Pendo API
        self.logger.warning("Account query not yet fully implemented")
        return True

    async def _query_activity(self, client: PendoClient) -> bool:
        """Query activity metrics.

        Args:
            client: Pendo API client

        Returns:
            True on success, False on failure
        """
        entity = getattr(self.args, "entity", "visitor")
        group_by = getattr(self.args, "group_by", None)

        self.logger.info(f"Querying activity for entity: {entity}")

        if group_by:
            self.logger.info(f"Grouping by: {group_by}")

        # TODO: Implement actual query via Pendo API
        self.logger.warning("Activity query not yet fully implemented")
        return True

    async def _query_wau(self, client: PendoClient) -> bool:
        """Query weekly (or N-day) active users: unique visitors with activity in the window.

        Uses Pendo aggregation: trackEvents in time range, then count distinct visitorIds.
        """
        last_days = getattr(self.args, "last_days", 7)
        last_days = max(1, min(last_days, 365))

        self.logger.info(f"Querying unique active visitors (last {last_days} days)...")

        time_series = {
            "period": "dayRange",
            "first": "now()",
            "count": -last_days,
        }
        # Pipeline: any track event in window -> distinct visitorIds -> count
        pipeline = [
            {
                "source": {
                    "trackEvents": {},
                    "timeSeries": time_series,
                },
            },
            {"identified": "visitorId"},
            {"select": {"visitorId": "visitorId"}},
            {"group": {"group": ["visitorId"], "fields": {}}},
            {"group": {"group": [], "fields": {"wau": {"count": "visitorId"}}}},
        ]

        body = {
            "response": {"mimeType": "application/json"},
            "request": {
                "requestId": "wau",
                "pipeline": pipeline,
            },
        }

        result = await client.post_aggregation(body)
        if result.get("errors"):
            for err in result["errors"]:
                self.logger.error(err)
            return False
        data = result.get("data") or {}
        results = data.get("results", [])
        if results:
            wau = results[0].get("wau", 0)
            self.logger.info(f"Unique active visitors (last {last_days} days): {wau}")
            print(wau)
        else:
            self.logger.info("No results")
            print(0)
        return True

    async def _query_events(self, client: PendoClient) -> bool:
        """Query event counts (e.g. cards created) with optional filters.

        Builds an aggregation pipeline for track events and optionally
        filters by country and date range.
        """
        event_name = getattr(self.args, "event_name", "core-card-service POST /io/card")
        from_date = getattr(self.args, "from_date", "2025-01-01")
        to_date = getattr(self.args, "to_date", "2025-12-31")
        country = getattr(self.args, "country", None)

        self.logger.info(
            f"Querying events: event={event_name!r}, from={from_date}, to={to_date}, country={country!r}"
        )

        # Pendo aggregation often accepts relative windows (first: "now()", count: -N).
        # For a date range in the past, compute days from start to today.
        try:
            start = datetime.strptime(from_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            end = datetime.strptime(to_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            days_span = (end - start).days
            now = datetime.now(timezone.utc)
            days_ago = (now - start).days
            use_relative = days_ago > 0 and days_span > 0
        except ValueError:
            use_relative = False
            days_ago = 365
            days_span = 365

        if use_relative:
            time_series = {"period": "dayRange", "first": "now()", "count": -days_ago}
        else:
            time_series = {"period": "dayRange", "first": from_date, "count": days_span}

        # Build pipeline: source trackEvents (no params per API), time range,
        # filter by event name and optionally country, then sum event count.
        pipeline = [
            {
                "source": {
                    "trackEvents": {},
                    "timeSeries": time_series,
                },
            },
            {"identified": "visitorId"},
            {"filter": f'eventName=="{event_name}"'},
            {"select": {"numEvents": "numEvents", "visitorId": "visitorId", "day": "day"}},
            {"group": {"group": [], "fields": {"totalEvents": {"sum": "numEvents"}}}},
        ]
        if country:
            pipeline.insert(2, {"filter": f'visitor.country=="{country}"'})

        body = {
            "response": {"mimeType": "application/json"},
            "request": {
                "requestId": "event-count",
                "pipeline": pipeline,
            },
        }

        result = await client.post_aggregation(body)
        if result.get("errors"):
            for err in result["errors"]:
                self.logger.error(err)
            return False
        data = result.get("data") or {}
        results = data.get("results", [])
        if results:
            total = results[0].get("totalEvents", 0)
            self.logger.info(f"Total events: {total}")
            print(total)
        else:
            self.logger.info("No results (event name or filters may not match any data)")
            print(0)
        return True
