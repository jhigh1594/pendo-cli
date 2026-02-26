"""Segment management commands."""

import sys
from typing import Any
import logging

from pendo_cli.commands.base import BaseCommand
from pendo_cli.api.client import PendoClient, PendoConfig


logger = logging.getLogger(__name__)


class SegmentCommand(BaseCommand):
    """Handle segment management commands.

    Supports: list, create, update, delete
    """

    async def execute(self) -> bool:
        """Execute the segment command.

        Returns:
            True on success, False on failure
        """
        from pendo_cli.config import get_config

        subscription = getattr(self.args, "subscription", None)
        config = get_config(subscription)

        action = getattr(self.args, "segment_action", None)

        # Use async context manager to properly close the session
        async with PendoClient(config) as client:
            if action == "list":
                return await self._list_segments(client)
            elif action == "create":
                return await self._create_segment(client)
            elif action == "update":
                return await self._update_segment(client)
            elif action == "delete":
                return await self._delete_segment(client)
            else:
                self.logger.error(f"Unknown segment action: {action}")
                return False

    async def _list_segments(self, client: PendoClient) -> bool:
        """List all segments.

        Args:
            client: Pendo API client

        Returns:
            True on success, False on failure
        """
        result = await client.list_segments()

        if result["errors"]:
            self.logger.error(f"Failed to list segments: {result['errors']}")
            return False

        segments = result.get("data", [])
        if isinstance(segments, dict):
            # API returned a dict with results inside
            segments = segments.get("results", [])

        # Print segments
        for segment in segments:
            segment_id = segment.get("id", "unknown")
            name = segment.get("name", "unnamed")
            print(f"{segment_id}: {name}")

        return True

    async def _create_segment(self, client: PendoClient) -> bool:
        """Create a new segment.

        Args:
            client: Pendo API client

        Returns:
            True on success, False on failure
        """
        segment_data = {
            "name": getattr(self.args, "name", "New Segment"),
            "description": getattr(self.args, "description", ""),
        }

        result = await client.create_segment(segment_data)

        if result["errors"]:
            self.logger.error(f"Failed to create segment: {result['errors']}")
            return False

        self.logger.info(f"Created segment: {result.get('data', {}).get('id')}")
        return True

    async def _update_segment(self, client: PendoClient) -> bool:
        """Update an existing segment.

        Args:
            client: Pendo API client

        Returns:
            True on success, False on failure
        """
        segment_id = getattr(self.args, "segment_id", None)
        if not segment_id:
            self.logger.error("segment_id is required for update")
            return False

        segment_data = {}
        if hasattr(self.args, "name") and self.args.name:
            segment_data["name"] = self.args.name
        if hasattr(self.args, "description") and self.args.description:
            segment_data["description"] = self.args.description

        result = await client.update_segment(segment_id, segment_data)

        if result["errors"]:
            self.logger.error(f"Failed to update segment: {result['errors']}")
            return False

        self.logger.info(f"Updated segment: {segment_id}")
        return True

    async def _delete_segment(self, client: PendoClient) -> bool:
        """Delete a segment.

        Args:
            client: Pendo API client

        Returns:
            True on success, False on failure
        """
        segment_id = getattr(self.args, "segment_id", None)
        if not segment_id:
            self.logger.error("segment_id is required for delete")
            return False

        result = await client.delete_segment(segment_id)

        if result["errors"]:
            self.logger.error(f"Failed to delete segment: {result['errors']}")
            return False

        self.logger.info(f"Deleted segment: {segment_id}")
        return True
