"""
Supermemory backend for vector-based memory storage

Supports both Supermemory Cloud (free/paid) and self-hosted instances.
Provides reliable vector-based memory with UI and proven architecture.
"""
import requests
from typing import List, Dict, Optional

from contextflow.modules.backends.base import MemoryBackend


class SupermemoryBackend(MemoryBackend):
    """
    Supermemory backend for vector-based memory.

    Connects to Supermemory API (cloud or self-hosted).
    Simpler than graph-based but reliable and fast.
    """

    def __init__(
        self,
        base_url: str = "https://api.supermemory.ai",
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini"
    ):
        """
        Initialize Supermemory backend.

        Args:
            base_url: Supermemory API base URL
                      Cloud: https://api.supermemory.ai
                      Self-hosted: http://localhost:8080
            api_key: API key (only for cloud, optional for self-hosted)
            model: Model name for embeddings
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

        # Determine if cloud or self-hosted
        self.is_cloud = "supermemory.ai" in base_url

    def _get_headers(self) -> Dict:
        """Get request headers with optional auth."""
        headers = {"Content-Type": "application/json"}

        if self.api_key and self.is_cloud:
            headers["x-supermemory-api-key"] = self.api_key

        return headers

    def search(
        self,
        query: str,
        user_id: str,
        limit: int = 5,
        timeout: float = 1.5,
        **kwargs
    ) -> List[Dict]:
        """
        Search for relevant memories via Supermemory API.

        Args:
            query: Search query
            user_id: User namespace
            limit: Max results
            timeout: Request timeout

        Returns:
            List of memory objects in standardized format
        """
        try:
            # Supermemory search endpoint
            endpoint = f"{self.base_url}/api/search"

            response = requests.post(
                endpoint,
                headers=self._get_headers(),
                json={
                    "query": query,
                    "userId": user_id,
                    "limit": limit
                },
                timeout=timeout
            )

            if response.status_code != 200:
                return []

            data = response.json()

            # Convert Supermemory format to standardized format
            memories = []
            for item in data.get("memories", []):
                memories.append({
                    "content": item.get("content", ""),
                    "relevance": item.get("score", 0.0),
                    "timestamp": item.get("timestamp", ""),
                    "metadata": item.get("metadata", {})
                })

            return memories

        except (requests.Timeout, requests.ConnectionError, Exception):
            # Graceful degradation
            return []

    def store(
        self,
        content: str,
        user_id: str,
        metadata: Optional[Dict] = None,
        **kwargs
    ) -> int:
        """
        Store memory in Supermemory.

        Supermemory handles chunking internally, so we just send the content.

        Args:
            content: Memory content
            user_id: User identifier
            metadata: Optional metadata

        Returns:
            Number of entries created (always 1, Supermemory handles chunking)
        """
        try:
            # Supermemory store endpoint
            endpoint = f"{self.base_url}/api/add"

            payload = {
                "content": content,
                "userId": user_id,
                "metadata": metadata or {}
            }

            # Add conversation_id if present
            if metadata and "conversation_id" in metadata:
                payload["conversationId"] = metadata["conversation_id"]

            requests.post(
                endpoint,
                headers=self._get_headers(),
                json=payload,
                timeout=2.0  # Slightly longer for storage
            )

            return 1  # Supermemory returns 1 entry (handles chunking internally)

        except Exception:
            # Fire-and-forget - ignore errors
            return 0

    def health_check(self) -> bool:
        """Check if Supermemory API is reachable."""
        try:
            # Try health endpoint (self-hosted) or base URL (cloud)
            endpoint = f"{self.base_url}/health" if not self.is_cloud else self.base_url

            response = requests.get(
                endpoint,
                headers=self._get_headers(),
                timeout=2.0
            )

            return response.status_code in [200, 404]  # 404 = cloud root (ok)

        except Exception:
            return False

    def get_info(self) -> Dict:
        """Get Supermemory backend information."""
        deployment_type = "Cloud (Supermemory.ai)" if self.is_cloud else "Self-hosted"

        return {
            "type": "Supermemory",
            "deployment": deployment_type,
            "base_url": self.base_url,
            "authenticated": bool(self.api_key),
            "healthy": self.health_check(),
            "features": [
                "Vector-based memory",
                "Automatic chunking",
                "Web UI (self-hosted)",
                "Proven architecture",
                "Fast queries",
                "Deduplication"
            ]
        }
