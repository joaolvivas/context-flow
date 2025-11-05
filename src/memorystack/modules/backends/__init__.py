"""
Memory backends for the Memory Router Proxy

Provides pluggable memory storage/retrieval backends:
- Graphiti (graph-based memory with Neo4j)
- Supermemory (vector-based memory)
- Future: Custom backends

All backends implement the same interface for seamless switching.
"""
from modules.backends.base import MemoryBackend
from modules.backends.graphiti_backend import GraphitiBackend
from modules.backends.supermemory_backend import SupermemoryBackend


def get_backend(backend_type: str, **config) -> MemoryBackend:
    """
    Factory function to get memory backend.

    Args:
        backend_type: Type of backend ("graphiti" or "supermemory")
        **config: Backend-specific configuration

    Returns:
        MemoryBackend instance

    Raises:
        ValueError: If backend_type is unknown
    """
    backends = {
        "graphiti": GraphitiBackend,
        "supermemory": SupermemoryBackend
    }

    if backend_type not in backends:
        raise ValueError(
            f"Unknown backend: {backend_type}. "
            f"Available: {list(backends.keys())}"
        )

    return backends[backend_type](**config)


__all__ = [
    "MemoryBackend",
    "GraphitiBackend",
    "SupermemoryBackend",
    "get_backend"
]
