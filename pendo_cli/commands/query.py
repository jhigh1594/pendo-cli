"""Query commands for Pendo data."""

import csv
import json
from datetime import datetime, timezone
from io import StringIO
from typing import Any
import logging

from dotenv import load_dotenv

from pendo_cli.commands.base import BaseCommand
from pendo_cli.api.client import PendoClient
from pendo_cli.config import get_config


logger = logging.getLogger(__name__)


def _format_output(
    results: list[dict], fmt: str, columns: list[str] | None = None
) -> str:
    """Format aggregation results as table, json, or csv."""
    if fmt == "json":
        return json.dumps(results, default=str)
    if fmt == "csv":
        out = StringIO()
        if not results:
            return ""
        keys = columns or sorted(results[0].keys(), key=str)
        writer = csv.DictWriter(out, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        for row in results:
            writer.writerow({k: row.get(k, "") for k in keys})
        return out.getvalue()
    # table: simple column alignment
    if not results:
        return ""
    keys = columns or sorted(results[0].keys(), key=str)
    widths = [max(len(str(k)), max(len(str(r.get(k, ""))) for r in results)) for k in keys]
    lines = [" | ".join(k.ljust(w) for k, w in zip(keys, widths))]
    lines.append("-+-".join("-" * w for w in widths))
    for row in results:
        lines.append(" | ".join(str(row.get(k, "")).ljust(w) for k, w in zip(keys, widths)))
    return "\n".join(lines)


def _time_series_for_date_range(
    from_date: str | None,
    to_date: str | None,
    default_last_days: int = 7,
) -> tuple[dict, str]:
    """Build timeSeries for aggregation: absolute range (epoch ms) or relative (now(), -N).

    Pendo expects first as epoch milliseconds for absolute ranges; string first is
    evaluated as an expression and can return no data.
    """
    if from_date and to_date:
        try:
            start = datetime.strptime(from_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            end = datetime.strptime(to_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            days_span = (end - start).days
            if days_span < 1:
                days_span = 1
            first_ms = int(start.timestamp() * 1000)
            return (
                {"period": "dayRange", "first": first_ms, "count": days_span},
                f"{from_date} to {to_date}",
            )
        except ValueError:
            pass
    last_days = max(1, min(default_last_days, 365))
    return (
        {"period": "dayRange", "first": "now()", "count": -last_days},
        f"last {last_days} days",
    )


class QueryCommand(BaseCommand):
    """Handle query commands for Pendo data.

    Supports: visitors, accounts, activity
    """

    async def execute(self) -> bool:
        """Execute the query command.

        Returns:
            True on success, False on failure
        """
        load_dotenv()
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
            elif query_type == "usage":
                return await self._query_usage(client)
            elif query_type == "features":
                return await self._query_features(client)
            elif query_type == "pages":
                return await self._query_pages(client)
            elif query_type == "wau":
                return await self._query_wau(client)
            elif query_type == "events":
                return await self._query_events(client)
            else:
                self.logger.error(f"Unknown query type: {query_type}")
                return False

    async def _query_visitors(self, client: PendoClient) -> bool:
        """Export visitors with metadata and optional cohort filters."""
        new_last_days = getattr(self.args, "new_last_days", None)
        inactive_days = getattr(self.args, "inactive_days", None)
        out_fmt = getattr(self.args, "format", "table")

        self.logger.info("Exporting visitors with metadata...")

        pipeline = [
            {"source": {"visitors": None}},
            {"identified": "visitorId"},
            {
                "select": {
                    "visitorId": "visitorId",
                    "accountId": "metadata.auto.accountid",
                    "firstvisit": "metadata.auto.firstvisit",
                    "lastvisit": "metadata.auto.lastvisit",
                    "lastupdated": "metadata.auto.lastupdated",
                    "lastbrowsername": "metadata.auto.lastbrowsername",
                    "lastoperatingsystem": "metadata.auto.lastoperatingsystem",
                },
            },
        ]

        filters = []
        if new_last_days:
            ms = new_last_days * 24 * 60 * 60 * 1000
            filters.append(f"firstvisit >= now() - {ms}")
        if inactive_days:
            ms = inactive_days * 24 * 60 * 60 * 1000
            filters.append(f"lastvisit <= now() - {ms}")
        if filters:
            pipeline.append({"filter": " && ".join(filters)})

        body = {
            "response": {"mimeType": "application/json"},
            "request": {"requestId": "visitors", "pipeline": pipeline},
        }

        result = await client.post_aggregation(body)
        if result.get("errors"):
            for err in result["errors"]:
                self.logger.error(err)
            return False
        data = result.get("data") or {}
        results = data.get("results", [])
        self.logger.info(f"Exported {len(results)} visitors")
        output = _format_output(results, out_fmt)
        if output:
            print(output)
        return True

    async def _query_accounts(self, client: PendoClient) -> bool:
        """Export accounts with metadata (ARR, plan, CSM, etc.) and optional cohort filters."""
        new_last_days = getattr(self.args, "new_last_days", None)
        out_fmt = getattr(self.args, "format", "table")

        self.logger.info("Exporting accounts with metadata...")

        pipeline = [
            {"source": {"accounts": None}},
            {"identified": "accountId"},
            {
                "select": {
                    "accountId": "accountId",
                    "name": "metadata.agent.name",
                    "firstvisit": "metadata.auto.firstvisit",
                    "lastvisit": "metadata.auto.lastvisit",
                    "lastupdated": "metadata.auto.lastupdated",
                    "arrannuallyrecurringrevenue": "metadata.custom.arrannuallyrecurringrevenue",
                    "customersuccessmanager": "metadata.custom.customersuccessmanager",
                    "industry": "metadata.custom.industry",
                    "planlevel": "metadata.custom.planlevel",
                    "renewaldate": "metadata.custom.renewaldate",
                    "totallicenses": "metadata.custom.totallicenses",
                },
            },
        ]

        if new_last_days:
            ms = new_last_days * 24 * 60 * 60 * 1000
            pipeline.append({"filter": f"firstvisit >= now() - {ms}"})

        body = {
            "response": {"mimeType": "application/json"},
            "request": {"requestId": "accounts", "pipeline": pipeline},
        }

        result = await client.post_aggregation(body)
        if result.get("errors"):
            for err in result["errors"]:
                self.logger.error(err)
            return False
        data = result.get("data") or {}
        results = data.get("results", [])
        self.logger.info(f"Exported {len(results)} accounts")
        output = _format_output(results, out_fmt)
        if output:
            print(output)
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

    async def _query_usage(self, client: PendoClient) -> bool:
        """Query active user counts: DAU, WAU, MAU, or custom N-day window."""
        mode = getattr(self.args, "mode", "wau")
        from_date = getattr(self.args, "from_date", None)
        to_date = getattr(self.args, "to_date", None)
        last_days = getattr(self.args, "last_days", None)
        group_by = getattr(self.args, "group_by", "none")
        out_fmt = getattr(self.args, "format", "table")

        # Derive window from mode when dates not specified
        mode_days = {"dau": 1, "wau": 7, "mau": 30}.get(mode, 7)
        default_days = last_days if mode == "custom" and last_days else mode_days

        time_series, window_label = _time_series_for_date_range(
            from_date, to_date, default_last_days=default_days
        )

        self.logger.info(f"Querying active users ({window_label}, mode={mode})...")

        pipeline = [
            {
                "source": {
                    "events": None,
                    "timeSeries": time_series,
                },
            },
            {"identified": "visitorId"},
        ]

        if group_by == "account":
            pipeline.extend(
                [
                    {"select": {"visitorId": "visitorId", "accountId": "accountId"}},
                    {
                        "group": {
                            "group": ["accountId"],
                            "fields": {"activeUsers": {"count": "visitorId"}},
                        },
                    },
                    {"sort": ["activeUsers"]},
                ]
            )
        else:
            pipeline.extend(
                [
                    {"select": {"visitorId": "visitorId"}},
                    {"group": {"group": [], "fields": {"activeUsers": {"count": "visitorId"}}}},
                ]
            )

        body = {
            "response": {"mimeType": "application/json"},
            "request": {"requestId": "usage", "pipeline": pipeline},
        }

        result = await client.post_aggregation(body)
        if result.get("errors"):
            for err in result["errors"]:
                self.logger.error(err)
            return False
        data = result.get("data") or {}
        results = data.get("results", [])
        if not results:
            self.logger.info("No results")
            print(_format_output([], out_fmt))
            return True

        if group_by == "account":
            output = _format_output(results, out_fmt, columns=["accountId", "activeUsers"])
        else:
            total = results[0].get("activeUsers", 0)
            self.logger.info(f"Active users ({window_label}): {total}")
            output = _format_output([{"activeUsers": total}], out_fmt)
        print(output)
        return True

    async def _query_features(self, client: PendoClient) -> bool:
        """Query feature usage or list feature catalog for a subscription."""
        from_date = getattr(self.args, "from_date", None)
        to_date = getattr(self.args, "to_date", None)
        last_days = getattr(self.args, "last_days", 30)
        top_n = getattr(self.args, "top", 10)
        feature_id = getattr(self.args, "feature_id", None)
        list_all = getattr(self.args, "list_all", False)
        out_fmt = getattr(self.args, "format", "table")

        if list_all:
            self.logger.info("Listing all features for subscription...")
            pipeline = [
                {"source": {"features": None}},
                {"select": {"id": "id", "name": "name"}},
            ]
            body = {
                "response": {"mimeType": "application/json"},
                "request": {"requestId": "features-list", "pipeline": pipeline},
            }
            result = await client.post_aggregation(body)
            if result.get("errors"):
                for err in result["errors"]:
                    self.logger.error(err)
                return False
            data = result.get("data") or {}
            results = data.get("results", [])
            output = _format_output(results, out_fmt, columns=["id", "name"])
            if output:
                print(output)
            return True

        time_series, window_label = _time_series_for_date_range(
            from_date, to_date, default_last_days=last_days
        )

        self.logger.info(f"Querying top {top_n} features ({window_label})...")

        pipeline = [
            {
                "source": {
                    "featureEvents": None,
                    "timeSeries": time_series,
                },
            },
            {"identified": "visitorId"},
            {
                "select": {
                    "featureId": "featureId",
                    "visitorId": "visitorId",
                    "numEvents": "numEvents",
                    "numMinutes": "numMinutes",
                },
            },
        ]
        if feature_id:
            pipeline.append({"filter": f'featureId=="{feature_id}"'})
        pipeline.extend(
            [
                {
                    "group": {
                        "group": ["featureId"],
                        "fields": {
                            "totalEvents": {"sum": "numEvents"},
                            "totalMinutes": {"sum": "numMinutes"},
                            "uniqueVisitors": {"count": "visitorId"},
                        },
                    },
                },
                {"sort": ["totalEvents"]},
            ]
        )

        body = {
            "response": {"mimeType": "application/json"},
            "request": {"requestId": "features", "pipeline": pipeline},
        }

        result = await client.post_aggregation(body)
        if result.get("errors"):
            for err in result["errors"]:
                self.logger.error(err)
            return False
        data = result.get("data") or {}
        results = data.get("results", [])[:top_n]
        output = _format_output(
            results,
            out_fmt,
            columns=["featureId", "totalEvents", "totalMinutes", "uniqueVisitors"],
        )
        print(output)
        return True

    async def _query_pages(self, client: PendoClient) -> bool:
        """Query page usage or list page catalog for a subscription."""
        from_date = getattr(self.args, "from_date", None)
        to_date = getattr(self.args, "to_date", None)
        last_days = getattr(self.args, "last_days", 30)
        top_n = getattr(self.args, "top", 10)
        page_id = getattr(self.args, "page_id", None)
        list_all = getattr(self.args, "list_all", False)
        out_fmt = getattr(self.args, "format", "table")

        if list_all:
            self.logger.info("Listing all pages for subscription...")
            pipeline = [
                {"source": {"pages": None}},
                {"select": {"id": "id", "name": "name"}},
            ]
            body = {
                "response": {"mimeType": "application/json"},
                "request": {"requestId": "pages-list", "pipeline": pipeline},
            }
            result = await client.post_aggregation(body)
            if result.get("errors"):
                for err in result["errors"]:
                    self.logger.error(err)
                return False
            data = result.get("data") or {}
            results = data.get("results", [])
            output = _format_output(results, out_fmt, columns=["id", "name"])
            if output:
                print(output)
            return True

        time_series, window_label = _time_series_for_date_range(
            from_date, to_date, default_last_days=last_days
        )

        self.logger.info(f"Querying top {top_n} pages ({window_label})...")

        pipeline = [
            {
                "source": {
                    "pageEvents": None,
                    "timeSeries": time_series,
                },
            },
            {"identified": "visitorId"},
            {
                "select": {
                    "pageId": "pageId",
                    "visitorId": "visitorId",
                    "numEvents": "numEvents",
                    "numMinutes": "numMinutes",
                },
            },
        ]
        if page_id:
            pipeline.append({"filter": f'pageId=="{page_id}"'})
        pipeline.extend(
            [
                {
                    "group": {
                        "group": ["pageId"],
                        "fields": {
                            "totalEvents": {"sum": "numEvents"},
                            "totalMinutes": {"sum": "numMinutes"},
                            "uniqueVisitors": {"count": "visitorId"},
                        },
                    },
                },
                {"sort": ["totalEvents"]},
            ]
        )

        body = {
            "response": {"mimeType": "application/json"},
            "request": {"requestId": "pages", "pipeline": pipeline},
        }

        result = await client.post_aggregation(body)
        if result.get("errors"):
            for err in result["errors"]:
                self.logger.error(err)
            return False
        data = result.get("data") or {}
        results = data.get("results", [])[:top_n]
        output = _format_output(
            results,
            out_fmt,
            columns=["pageId", "totalEvents", "totalMinutes", "uniqueVisitors"],
        )
        print(output)
        return True

    async def _query_wau(self, client: PendoClient) -> bool:
        """Query weekly (or N-day) or date-range active users: unique visitors with activity in the window."""
        from_date = getattr(self.args, "from_date", None)
        to_date = getattr(self.args, "to_date", None)
        last_days = getattr(self.args, "last_days", 7)

        time_series, window_label = _time_series_for_date_range(
            from_date, to_date, default_last_days=last_days
        )

        self.logger.info(f"Querying unique active visitors ({window_label})...")

        pipeline = [
            {
                "source": {
                    "trackEvents": {},
                    "timeSeries": time_series,
                },
            },
            {"identified": "visitorId"},
            {"select": {"visitorId": "visitorId"}},
            {"group": {"group": [], "fields": {"wau": {"count": "visitorId"}}}},
        ]

        body = {
            "response": {"mimeType": "application/json"},
            "request": {"requestId": "wau", "pipeline": pipeline},
        }

        result = await client.post_aggregation(body)
        if result.get("errors"):
            for err in result["errors"]:
                self.logger.error(err)
            return False
        data = result.get("data") or {}
        results = data.get("results", [])
        out_fmt = getattr(self.args, "format", "table")
        if results:
            wau = results[0].get("wau", 0)
            self.logger.info(f"Unique active visitors ({window_label}): {wau}")
            print(_format_output([{"wau": wau}], out_fmt))
        else:
            self.logger.info("No results")
            print(_format_output([{"wau": 0}], out_fmt))
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
        list_types = getattr(self.args, "list_types", False)
        out_fmt = getattr(self.args, "format", "table")

        if list_types:
            # List distinct event names with counts over a window.
            time_series, window_label = _time_series_for_date_range(
                from_date, to_date, default_last_days=30
            )
            self.logger.info(
                f"Listing event types ({window_label}), country={country!r}"
            )
            pipeline = [
                {
                    "source": {
                        "trackEvents": {},
                        "timeSeries": time_series,
                    },
                },
                {"identified": "visitorId"},
                {
                    "select": {
                        "eventName": "eventName",
                        "visitorId": "visitorId",
                        "numEvents": "numEvents",
                    }
                },
            ]
            if country:
                pipeline.append({"filter": f'visitor.country=="{country}"'})
            pipeline.extend(
                [
                    {
                        "group": {
                            "group": ["eventName"],
                            "fields": {
                                "totalEvents": {"sum": "numEvents"},
                                "uniqueVisitors": {"count": "visitorId"},
                            },
                        }
                    },
                    {"sort": ["totalEvents"]},
                ]
            )
            body = {
                "response": {"mimeType": "application/json"},
                "request": {
                    "requestId": "event-types",
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
            output = _format_output(
                results, out_fmt, columns=["eventName", "totalEvents", "uniqueVisitors"]
            )
            if output:
                print(output)
            return True

        self.logger.info(
            f"Querying events: event={event_name!r}, from={from_date}, to={to_date}, country={country!r}"
        )

        # Use epoch ms for absolute ranges so Pendo returns historical data (YoY, etc.).
        time_series, _ = _time_series_for_date_range(
            from_date, to_date, default_last_days=365
        )

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
            print(_format_output([{"totalEvents": total}], out_fmt))
        else:
            self.logger.info("No results (event name or filters may not match any data)")
            print(_format_output([{"totalEvents": 0}], out_fmt))
        return True
