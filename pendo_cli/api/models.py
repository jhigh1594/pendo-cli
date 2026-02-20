"""TypedDict models for Pendo API responses."""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class PendoConfig:
    """Configuration for Pendo API client."""

    subscription_id: str
    app_id: str
    base_url: str = "https://app.pendo.io"
    timeout: int = 30
    max_retries: int = 3
    api_key: Optional[str] = None


class ApiResponse(Dict[str, Any]):
    """Standard API response structure with graceful error handling."""

    def __init__(self, data: Any = None, errors: List[str] | None = None):
        super().__init__(data=data, errors=errors or [])
