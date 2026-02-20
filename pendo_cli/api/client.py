"""Async Pendo API client with graceful error handling."""

import aiohttp
from typing import Dict, Any, Optional
import logging

from pendo_cli.api.models import PendoConfig


logger = logging.getLogger(__name__)


class PendoClient:
    """Async Pendo API client with graceful error handling.

    All methods return a dict with 'data' and 'errors' keys:
    - {'data': <response_data>, 'errors': []} on success
    - {'data': None, 'errors': ['error message']} on failure
    """

    def __init__(self, config: PendoConfig):
        """Initialize the Pendo client.

        Args:
            config: PendoConfig instance with subscription details
        """
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def subscription_id(self) -> str:
        """Get subscription ID for convenience."""
        return self.config.subscription_id

    async def __aenter__(self):
        """Async context manager entry."""
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args):
        """Async context manager exit."""
        if self._session:
            await self._session.close()

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Make API request with graceful error handling.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            **kwargs: Additional arguments for aiohttp

        Returns:
            Dict with 'data' and 'errors' keys
        """
        url = f"{self.config.base_url}{endpoint}"

        if self._session is None:
            self._session = aiohttp.ClientSession()

        try:
            async with self._session.request(
                method,
                url,
                timeout=self.config.timeout,
                **kwargs
            ) as response:
                try:
                    data = await response.json()
                except Exception:
                    # If response isn't JSON, return text or empty dict
                    text = await response.text()
                    data = {"text": text} if text else {}

                return {"data": data, "errors": []}

        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error: {e}")
            return {"data": None, "errors": [str(e)]}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"data": None, "errors": [str(e)]}

    async def list_segments(self) -> Dict[str, Any]:
        """List all segments for the subscription.

        Returns:
            Dict with 'data' containing segment list and 'errors' list
        """
        return await self._request(
            "GET",
            f"/api/v1/subscription/{self.config.subscription_id}/segment"
        )

    async def create_segment(self, segment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new segment.

        Args:
            segment_data: Dictionary containing segment configuration

        Returns:
            Dict with 'data' containing created segment and 'errors' list
        """
        return await self._request(
            "POST",
            f"/api/v1/subscription/{self.config.subscription_id}/segment",
            json=segment_data
        )

    async def update_segment(
        self,
        segment_id: str,
        segment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing segment.

        Args:
            segment_id: ID of the segment to update
            segment_data: Dictionary containing segment updates

        Returns:
            Dict with 'data' containing updated segment and 'errors' list
        """
        return await self._request(
            "PUT",
            f"/api/v1/subscription/{self.config.subscription_id}/segment/{segment_id}",
            json=segment_data
        )

    async def delete_segment(self, segment_id: str) -> Dict[str, Any]:
        """Delete a segment.

        Args:
            segment_id: ID of the segment to delete

        Returns:
            Dict with 'data' and 'errors' keys
        """
        return await self._request(
            "DELETE",
            f"/api/v1/subscription/{self.config.subscription_id}/segment/{segment_id}"
        )

    async def post_aggregation(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Run an aggregation pipeline.

        Requires config.api_key (X-Pendo-Integration-Key). Pipeline runs
        in the context of the subscription.

        Args:
            body: JSON body with response and request.pipeline

        Returns:
            Dict with 'data' containing aggregation results and 'errors' list
        """
        if not getattr(self.config, "api_key", None):
            return {"data": None, "errors": ["PENDO_API_KEY required for aggregation"]}
        url = f"{self.config.base_url}/api/v1/aggregation"
        if self._session is None:
            self._session = aiohttp.ClientSession()
        headers = {
            "Content-Type": "application/json",
            "X-Pendo-Integration-Key": self.config.api_key,
        }
        try:
            async with self._session.request(
                "POST",
                url,
                json=body,
                timeout=self.config.timeout,
                headers=headers,
            ) as response:
                try:
                    data = await response.json()
                except Exception:
                    text = await response.text()
                    data = {"text": text} if text else {}
                if response.status >= 400:
                    return {
                        "data": None,
                        "errors": [data.get("message", data.get("text", str(data)))],
                    }
                return {"data": data, "errors": []}
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error: {e}")
            return {"data": None, "errors": [str(e)]}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"data": None, "errors": [str(e)]}
