"""
Graphiti backend for graph-based memory storage

Uses Graphiti MCP + Neo4j for knowledge graph memory.
Provides entity extraction, relationship building, and semantic search.
"""
import requests
from typing import List, Dict, Optional

from modules.backends.base import MemoryBackend
from modules.chunking import chunk_text, should_chunk


class GraphitiBackend(MemoryBackend):
    """
    Graphiti/MCP backend for graph-based memory.

    Connects to Graphiti MCP server which interfaces with Neo4j.
    Provides superior memory through entity extraction and relationships.
    """

    def __init__(
        self,
        search_endpoint: str = "http://localhost:5000/mcp/search",
        store_endpoint: str = "http://localhost:5000/mcp/store",
        chunk_size: int = 500,
        model: str = "gpt-4o-mini"
    ):
        """
        Initialize Graphiti backend.

        Args:
            search_endpoint: MCP search endpoint URL
            store_endpoint: MCP store endpoint URL
            chunk_size: Max tokens per chunk for storage
            model: Model name for token counting
        """
        self.search_endpoint = search_endpoint
        self.store_endpoint = store_endpoint
        self.chunk_size = chunk_size
        self.model = model

    def search(
        self,
        query: str,
        user_id: str,
        limit: int = 5,
        timeout: float = 10.0,  # Increased timeout for Graphiti
        **kwargs
    ) -> List[Dict]:
        """
        Search for relevant memories via Graphiti MCP.

        Args:
            query: Search query
            user_id: User namespace
            limit: Max results
            timeout: Request timeout

        Returns:
            List of memory objects
        """
        try:
            response = requests.post(
                self.search_endpoint,
                json={
                    "query": query,
                    "user_id": user_id,
                    "group_id": user_id,  # Use user_id as group_id for memory namespace
                    "limit": limit
                },
                timeout=timeout
            )

            if response.status_code != 200:
                return []

            data = response.json()
            return data.get("results", [])

        except (requests.Timeout, requests.ConnectionError, Exception) as e:
            # Graceful degradation
            import logging
            logging.error(f"Backend search failed: {e}")
            return []

    def store(
        self,
        content: str,
        user_id: str,
        metadata: Optional[Dict] = None,
        **kwargs
    ) -> int:
        """
        Store memory in Graphiti with intelligent chunking.

        Args:
            content: Memory content
            user_id: User identifier
            metadata: Optional metadata

        Returns:
            Number of chunks created
        """
        chunks_created = 0

        try:
            # Check if content needs chunking
            if should_chunk(content, self.model, self.chunk_size):
                # Split into semantic chunks
                chunks = chunk_text(content, self.model, self.chunk_size)

                # Store each chunk separately
                for chunk in chunks:
                    chunk_metadata = metadata.copy() if metadata else {}
                    chunk_metadata.update({
                        "chunk_index": chunk["index"],
                        "total_chunks": len(chunks),
                        "chunk_tokens": chunk["tokens"]
                    })

                    resp = requests.post(
                        self.store_endpoint,
                        json={
                            "content": chunk["content"],
                            "user_id": user_id,
                            "metadata": chunk_metadata
                        },
                        timeout=30.0  # Increased timeout for Graphiti processing
                    )
                    if resp.status_code == 200:
                        chunks_created += 1
            else:
                # Store as single memory
                resp = requests.post(
                    self.store_endpoint,
                    json={
                        "content": content,
                        "user_id": user_id,
                        "metadata": metadata or {}
                    },
                    timeout=30.0  # Increased timeout for Graphiti processing
                )
                if resp.status_code == 200:
                    chunks_created = 1

        except Exception as e:
            # Log errors but don't fail
            import logging
            logging.error(f"Backend store failed: {e}")
            pass

        return chunks_created

    def health_check(self) -> bool:
        """Check if MCP server is reachable."""
        try:
            response = requests.get(
                self.search_endpoint.replace("/mcp/search", "/health"),
                timeout=2.0
            )
            return response.status_code == 200
        except Exception:
            return False

    def get_info(self) -> Dict:
        """Get Graphiti backend information."""
        return {
            "type": "Graphiti",
            "search_endpoint": self.search_endpoint,
            "store_endpoint": self.store_endpoint,
            "chunk_size": self.chunk_size,
            "healthy": self.health_check(),
            "features": [
                "Graph-based memory",
                "Entity extraction",
                "Relationship building",
                "Temporal queries",
                "Semantic + structural search"
            ]
        }
