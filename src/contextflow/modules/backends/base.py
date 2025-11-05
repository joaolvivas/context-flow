"""
Base interface for memory backends

All memory backends must implement this interface to ensure
consistent behavior across different storage solutions.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class MemoryBackend(ABC):
    """
    Abstract base class for memory storage backends.

    All backends must implement search and store methods with
    consistent signatures and return formats.
    """

    @abstractmethod
    def search(
        self,
        query: str,
        user_id: str,
        limit: int = 5,
        timeout: float = 1.5,
        **kwargs
    ) -> List[Dict]:
        """
        Search for relevant memories.

        Args:
            query: Search query text
            user_id: User identifier for memory isolation
            limit: Maximum number of results
            timeout: Request timeout in seconds
            **kwargs: Backend-specific parameters

        Returns:
            List of memory objects with standardized format:
            [
                {
                    "content": "memory text",
                    "relevance": 0.95,  # 0-1 score
                    "timestamp": "2024-01-15T10:00:00",
                    "metadata": {...}
                },
                ...
            ]

        Note:
            Must return empty list on error (graceful degradation).
            Must not raise exceptions.
        """
        pass

    @abstractmethod
    def store(
        self,
        content: str,
        user_id: str,
        metadata: Optional[Dict] = None,
        **kwargs
    ) -> int:
        """
        Store new memory.

        Args:
            content: Memory content to store
            user_id: User identifier
            metadata: Optional metadata (timestamp, conversation_id, etc)
            **kwargs: Backend-specific parameters

        Returns:
            Number of chunks/entries created

        Note:
            Should be non-blocking or use async internally.
            Must not raise exceptions (fire-and-forget).
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if backend is healthy and reachable.

        Returns:
            True if backend is accessible, False otherwise
        """
        pass

    def get_info(self) -> Dict:
        """
        Get backend information and statistics.

        Returns:
            Dictionary with backend details
        """
        return {
            "type": self.__class__.__name__,
            "healthy": self.health_check()
        }
