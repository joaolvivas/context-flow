"""
LangMem Store - Unified Memory Management with LangGraph BaseStore

Replaces manual 3-tier system (WorkingMemory + SessionMemory + Graphiti)
with official LangGraph memory infrastructure.

Architecture:
- Namespaces:
  - ("conversations", user_id, conv_id) → Recent conversation turns
  - ("facts", user_id, conv_id) → Extracted facts
  - ("memories", user_id) → Long-term semantic memories

- Features:
  - Semantic vector search (vs keyword matching)
  - Async operations (vs background threads)
  - Cross-thread persistence
  - JSON document storage
  - Automatic deduplication

Performance:
- Vector search > keyword matching for relevance
- Unified Redis queries (vs multiple tier calls)
- Framework-level optimizations
"""
import os
import json
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Lazy imports to avoid initialization issues
_RedisStore = None
_InMemoryStore = None
_OpenAIEmbeddings = None


def _get_redis_store_class():
    """Lazy import RedisStore to avoid initialization issues."""
    global _RedisStore
    if _RedisStore is None:
        try:
            from langgraph.store.redis import RedisStore
            _RedisStore = RedisStore
        except ImportError:
            logger.error("langgraph-checkpoint-redis not installed. Install with: pip install langgraph-checkpoint-redis")
            raise
    return _RedisStore


def _get_inmemory_store_class():
    """Lazy import InMemoryStore for testing."""
    global _InMemoryStore
    if _InMemoryStore is None:
        from langgraph.store.memory import InMemoryStore
        _InMemoryStore = InMemoryStore
    return _InMemoryStore


def _get_openai_embeddings():
    """Get or create OpenAI embeddings instance (singleton)."""
    global _OpenAIEmbeddings
    if _OpenAIEmbeddings is None:
        try:
            from langchain_openai import OpenAIEmbeddings
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                logger.warning("OPENAI_API_KEY not set, embeddings will fail")
                return None
            _OpenAIEmbeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                openai_api_key=openai_api_key
            )
            logger.debug("  ✓ OpenAI embeddings initialized")
        except ImportError:
            logger.error("langchain-openai not installed")
            return None
    return _OpenAIEmbeddings


class LangMemStore:
    """
    Unified memory store using LangGraph BaseStore.

    Replaces:
    - WorkingMemory (Tier 1) → conversations namespace
    - SessionMemory (Tier 2) → facts namespace
    - Graphiti (Tier 3) → memories namespace
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        embedding_model: str = "openai:text-embedding-3-small",
        embedding_dims: int = 1536,
        use_in_memory: bool = False
    ):
        """
        Initialize LangMem store.

        Args:
            redis_url: Redis connection URL (redis://host:port)
            embedding_model: Model for vector embeddings
            embedding_dims: Embedding dimensions
            use_in_memory: Use InMemoryStore for testing (data lost on restart)
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.embedding_model = embedding_model
        self.embedding_dims = embedding_dims
        self.use_in_memory = use_in_memory

        self._store = None
        self._initialized = False

        logger.info(f"🧠 LangMemStore initialized (redis={self.redis_url}, use_in_memory={use_in_memory})")

    async def _ensure_initialized(self):
        """Lazy initialize store on first use."""
        if not self._initialized:
            await self._initialize_store()
            self._initialized = True

    async def _initialize_store(self):
        """Initialize the BaseStore backend."""
        try:
            # Get embeddings function
            embeddings = _get_openai_embeddings()
            if embeddings is None and not self.use_in_memory:
                logger.error("Failed to create embeddings, falling back to InMemoryStore")
                self.use_in_memory = True

            if self.use_in_memory:
                # Development/testing mode
                InMemoryStoreClass = _get_inmemory_store_class()
                # InMemoryStore doesn't need embeddings (no vector search)
                self._store = InMemoryStoreClass()
                logger.info("  ✓ InMemoryStore initialized (dev mode)")
            else:
                # Production mode with Redis
                # RedisStore.from_conn_string returns a context manager
                # We need to enter it and keep the store instance
                RedisStoreClass = _get_redis_store_class()

                # Use Redis with embeddings for vector search
                import redis.asyncio as redis_async

                # Create Redis client directly
                self._redis_client = redis_async.from_url(self.redis_url)

                # Create store with embeddings
                # RedisStore expects (conn_string, index={embed: Embeddings})
                self._store = RedisStoreClass(
                    self._redis_client,
                    index={"embed": embeddings} if embeddings else None
                )

                logger.info(f"  ✓ RedisStore initialized (redis={self.redis_url})")

        except Exception as e:
            logger.error(f"Failed to initialize LangMem store: {e}", exc_info=True)
            # Fallback to in-memory
            logger.warning("  ⚠️ Falling back to InMemoryStore")
            InMemoryStoreClass = _get_inmemory_store_class()
            self._store = InMemoryStoreClass()
            self.use_in_memory = True

    # =========================================================================
    # TIER 1: Conversation Turns (replaces WorkingMemory)
    # =========================================================================

    async def add_turn(
        self,
        user_id: str,
        conversation_id: str,
        role: str,
        content: str
    ) -> None:
        """
        Add a conversation turn to memory.

        Replaces: WorkingMemory.add_turn()

        Args:
            user_id: User identifier
            conversation_id: Conversation identifier
            role: Message role (user/assistant)
            content: Message content
        """
        await self._ensure_initialized()

        namespace = ("conversations", user_id, conversation_id)
        doc_id = f"turn_{int(datetime.now().timestamp() * 1000)}"

        document = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "conversation_id": conversation_id
        }

        await self._store.aput(namespace, doc_id, document)
        logger.debug(f"  ✓ Turn stored: {namespace} / {doc_id}")

    async def get_recent_turns(
        self,
        user_id: str,
        conversation_id: str,
        limit: int = 20
    ) -> List[Dict]:
        """
        Get recent conversation turns.

        Replaces: WorkingMemory.get_recent_turns()

        Args:
            user_id: User identifier
            conversation_id: Conversation identifier
            limit: Max turns to return

        Returns:
            List of conversation turns (sorted by timestamp)
        """
        await self._ensure_initialized()

        namespace = ("conversations", user_id, conversation_id)

        # Search without query returns all items in namespace
        items = await self._store.asearch(namespace, query="", limit=limit * 2)  # Get extra for sorting

        # Sort by timestamp and limit
        sorted_items = sorted(
            items,
            key=lambda x: x.value.get("timestamp", ""),
            reverse=True
        )[:limit]

        # Return as list of dicts (matching old API)
        turns = [
            {
                "role": item.value.get("role"),
                "content": item.value.get("content"),
                "timestamp": item.value.get("timestamp")
            }
            for item in sorted_items
        ]

        return list(reversed(turns))  # Oldest first

    async def format_turns_as_context(
        self,
        user_id: str,
        conversation_id: str,
        limit: int = 20
    ) -> str:
        """
        Format recent turns as context string.

        Replaces: WorkingMemory.format_as_context()

        Args:
            user_id: User identifier
            conversation_id: Conversation identifier
            limit: Max turns to include

        Returns:
            Formatted context string
        """
        turns = await self.get_recent_turns(user_id, conversation_id, limit)

        if not turns:
            return ""

        formatted = []
        for turn in turns:
            role = turn["role"].capitalize()
            content = turn["content"]
            formatted.append(f"{role}: {content}")

        return "\n".join(formatted)

    # =========================================================================
    # TIER 2: Facts (replaces SessionMemory)
    # =========================================================================

    async def store_facts(
        self,
        user_id: str,
        conversation_id: str,
        facts: List[Dict]
    ) -> int:
        """
        Store extracted facts in memory.

        Replaces: SessionMemory.store_facts()

        Args:
            user_id: User identifier
            conversation_id: Conversation identifier
            facts: List of facts (each with 'fact' and 'category' fields)

        Returns:
            Number of facts stored
        """
        if not facts:
            return 0

        await self._ensure_initialized()

        namespace = ("facts", user_id, conversation_id)
        count = 0

        for fact in facts:
            doc_id = f"fact_{int(datetime.now().timestamp() * 1000)}_{count}"

            document = {
                "fact": fact.get("fact", ""),
                "category": fact.get("category", "general"),
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "conversation_id": conversation_id
            }

            await self._store.aput(namespace, doc_id, document)
            count += 1

        logger.debug(f"  ✓ {count} facts stored: {namespace}")
        return count

    async def search_facts(
        self,
        user_id: str,
        conversation_id: str,
        query: str,
        limit: int = 5
    ) -> List[Dict]:
        """
        Semantic search over facts.

        Replaces: SessionMemory.search_facts()
        Uses vector search instead of keyword matching.

        Args:
            user_id: User identifier
            conversation_id: Conversation identifier
            query: Search query
            limit: Max results

        Returns:
            Matching facts
        """
        await self._ensure_initialized()

        namespace = ("facts", user_id, conversation_id)

        # Semantic search using embeddings
        items = await self._store.asearch(namespace, query=query, limit=limit)

        # Extract fact objects
        facts = [
            {
                "fact": item.value.get("fact"),
                "category": item.value.get("category"),
                "timestamp": item.value.get("timestamp"),
                "relevance": getattr(item, "score", 1.0)  # LangMem provides relevance score
            }
            for item in items
        ]

        return facts

    async def format_facts_as_context(
        self,
        user_id: str,
        conversation_id: str,
        query: Optional[str] = None,
        limit: int = 5
    ) -> str:
        """
        Format facts as context string.

        Replaces: SessionMemory.format_as_context()

        Args:
            user_id: User identifier
            conversation_id: Conversation identifier
            query: Optional search query for filtering
            limit: Max facts to include

        Returns:
            Formatted context string
        """
        if query:
            facts = await self.search_facts(user_id, conversation_id, query, limit)
        else:
            # Get all facts (no query)
            facts = await self.search_facts(user_id, conversation_id, "", limit)

        if not facts:
            return ""

        formatted = ["Recent facts about user:"]
        for fact in facts:
            formatted.append(f"  - {fact['fact']}")

        return "\n".join(formatted)

    # =========================================================================
    # TIER 3: Long-term Memories (replaces Graphiti)
    # =========================================================================

    async def store_memory(
        self,
        user_id: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Store long-term semantic memory.

        Replaces: Graphiti backend.store()

        Args:
            user_id: User identifier
            content: Memory content
            metadata: Optional metadata

        Returns:
            Document ID
        """
        await self._ensure_initialized()

        namespace = ("memories", user_id)
        doc_id = f"memory_{int(datetime.now().timestamp() * 1000)}"

        document = {
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "metadata": metadata or {}
        }

        await self._store.aput(namespace, doc_id, document)
        logger.debug(f"  ✓ Memory stored: {namespace} / {doc_id}")

        return doc_id

    async def search_memories(
        self,
        user_id: str,
        query: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Semantic search in long-term memory.

        Replaces: Graphiti backend.search()
        Uses vector search for better relevance.

        Args:
            user_id: User identifier
            query: Search query
            limit: Max results

        Returns:
            Matching memories
        """
        await self._ensure_initialized()

        namespace = ("memories", user_id)

        # Semantic search using embeddings
        items = await self._store.asearch(namespace, query=query, limit=limit)

        # Format as list of dicts (matching Graphiti API)
        memories = [
            {
                "content": item.value.get("content"),
                "timestamp": item.value.get("timestamp"),
                "metadata": item.value.get("metadata", {}),
                "relevance": getattr(item, "score", 1.0)
            }
            for item in items
        ]

        return memories

    async def format_memories_as_context(
        self,
        user_id: str,
        query: str,
        limit: int = 10
    ) -> str:
        """
        Format long-term memories as context string.

        Args:
            user_id: User identifier
            query: Search query
            limit: Max memories

        Returns:
            Formatted context string
        """
        memories = await self.search_memories(user_id, query, limit)

        if not memories:
            return ""

        formatted = []
        for idx, memory in enumerate(memories, 1):
            content = memory.get("content", "")
            formatted.append(f"{idx}. {content}")

        return "\n".join(formatted)

    # =========================================================================
    # Unified Operations
    # =========================================================================

    async def get_combined_context(
        self,
        user_id: str,
        conversation_id: str,
        query: str,
        tier_config: Dict[str, bool]
    ) -> Tuple[str, Dict]:
        """
        Get combined context from all enabled tiers.

        Replaces: MemoryRouter.get_memory_context()

        Args:
            user_id: User identifier
            conversation_id: Conversation identifier
            query: User query
            tier_config: Dict with 'use_conversations', 'use_facts', 'use_memories'

        Returns:
            Tuple of (formatted_context, metadata)
        """
        context_parts = []
        metadata = {
            "tiers_used": [],
            "turns": 0,
            "facts": 0,
            "memories": 0
        }

        # Tier 1: Recent conversations
        if tier_config.get("use_conversations", True):
            turns_context = await self.format_turns_as_context(user_id, conversation_id, limit=15)
            if turns_context:
                context_parts.append(f"<recent_conversation>\n{turns_context}\n</recent_conversation>")
                turns = await self.get_recent_turns(user_id, conversation_id, limit=15)
                metadata["turns"] = len(turns)
                metadata["tiers_used"].append("conversations")

        # Tier 2: Facts
        if tier_config.get("use_facts", False):
            facts_context = await self.format_facts_as_context(user_id, conversation_id, query, limit=5)
            if facts_context:
                context_parts.append(f"<user_facts>\n{facts_context}\n</user_facts>")
                facts = await self.search_facts(user_id, conversation_id, query, limit=5)
                metadata["facts"] = len(facts)
                metadata["tiers_used"].append("facts")

        # Tier 3: Long-term memories
        if tier_config.get("use_memories", False):
            memories_context = await self.format_memories_as_context(user_id, query, limit=10)
            if memories_context:
                context_parts.append(f"<knowledge_graph>\n{memories_context}\n</knowledge_graph>")
                memories = await self.search_memories(user_id, query, limit=10)
                metadata["memories"] = len(memories)
                metadata["tiers_used"].append("memories")

        combined_context = "\n\n".join(context_parts) if context_parts else ""

        return combined_context, metadata

    async def health_check(self) -> Dict[str, bool]:
        """Check if store is available."""
        try:
            await self._ensure_initialized()
            # Try a simple operation
            test_namespace = ("health", "check")
            await self._store.aput(test_namespace, "ping", {"status": "ok"})
            return {"healthy": True, "in_memory": self.use_in_memory}
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"healthy": False, "error": str(e)}

    # =========================================================================
    # Profile Seeding
    # =========================================================================

    async def seed_base_profile(
        self,
        user_id: str,
        conversation_id: str,
        profile_data: Dict[str, any]
    ) -> Dict[str, int]:
        """
        Seed base profile data into LangMem namespaces.

        Args:
            user_id: User identifier
            conversation_id: Conversation identifier
            profile_data: Dict with keys: name, bio, facts, memories

        Returns:
            Dict with counts of seeded items per tier
        """
        await self._ensure_initialized()

        counts = {"turns": 0, "facts": 0, "memories": 0}

        # Check if already seeded (look for base_profile marker)
        namespace_marker = ("metadata", user_id)
        try:
            existing_items = await self._store.asearch(namespace_marker, query="base_profile", limit=1)
            if existing_items:
                logger.info(f"  ℹ️ Base profile already seeded for user {user_id}")
                return counts
        except Exception:
            pass  # Marker doesn't exist, proceed with seed

        # Tier 1: Add base profile as initial turns
        if "name" in profile_data or "bio" in profile_data:
            # Create a synthetic "introduction" turn
            intro_content = []
            if "name" in profile_data:
                intro_content.append(f"Meu nome é {profile_data['name']}.")
            if "bio" in profile_data:
                intro_content.append(profile_data["bio"])

            intro_text = " ".join(intro_content)

            await self.add_turn(user_id, conversation_id, "user", "Quem sou eu?")
            await self.add_turn(user_id, conversation_id, "assistant", intro_text)
            counts["turns"] = 2

        # Tier 2: Add structured facts
        if "facts" in profile_data and isinstance(profile_data["facts"], list):
            facts_stored = await self.store_facts(user_id, conversation_id, profile_data["facts"])
            counts["facts"] = facts_stored

        # Tier 3: Add long-term memories
        if "memories" in profile_data:
            if isinstance(profile_data["memories"], str):
                await self.store_memory(
                    user_id,
                    profile_data["memories"],
                    metadata={"source": "base_profile", "seeded": True}
                )
                counts["memories"] = 1
            elif isinstance(profile_data["memories"], list):
                for memory in profile_data["memories"]:
                    await self.store_memory(
                        user_id,
                        memory,
                        metadata={"source": "base_profile", "seeded": True}
                    )
                    counts["memories"] += 1

        # Mark as seeded
        await self._store.aput(
            namespace_marker,
            "base_profile_seeded",
            {
                "seeded_at": datetime.now().isoformat(),
                "user_id": user_id,
                "conversation_id": conversation_id
            }
        )

        logger.info(f"  ✅ Base profile seeded: {counts}")
        return counts

    # =========================================================================
    # Inspection/Debugging
    # =========================================================================

    async def peek_all_namespaces(
        self,
        user_id: str,
        conversation_id: str,
        turns_limit: int = 10,
        facts_limit: int = 5,
        memories_limit: int = 5
    ) -> Dict[str, any]:
        """
        Peek into all LangMem namespaces for debugging/inspection.

        Returns:
            Dict with turns, facts, and memories
        """
        await self._ensure_initialized()

        result = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "tier1": {"turns": [], "count": 0},
            "tier2": {"facts": [], "count": 0},
            "tier3": {"memories": [], "count": 0}
        }

        # Tier 1: Conversations
        try:
            turns = await self.get_recent_turns(user_id, conversation_id, limit=turns_limit)
            result["tier1"]["turns"] = turns
            result["tier1"]["count"] = len(turns)
        except Exception as e:
            logger.warning(f"Failed to peek tier1: {e}")

        # Tier 2: Facts
        try:
            # Get all facts (no query)
            facts = await self.search_facts(user_id, conversation_id, "", limit=facts_limit)
            result["tier2"]["facts"] = facts
            result["tier2"]["count"] = len(facts)
        except Exception as e:
            logger.warning(f"Failed to peek tier2: {e}")

        # Tier 3: Memories
        try:
            # Get recent memories (no specific query)
            memories = await self.search_memories(user_id, "", limit=memories_limit)
            result["tier3"]["memories"] = memories
            result["tier3"]["count"] = len(memories)
        except Exception as e:
            logger.warning(f"Failed to peek tier3: {e}")

        return result


# ============================================================================
# Singleton Instance
# ============================================================================

_langmem_store_instance = None


def get_langmem_store() -> LangMemStore:
    """
    Get or create singleton LangMemStore instance.

    Returns:
        LangMemStore instance
    """
    global _langmem_store_instance

    if _langmem_store_instance is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        embedding_model = os.getenv("LANGMEM_EMBEDDING_MODEL", "openai:text-embedding-3-small")
        embedding_dims = int(os.getenv("LANGMEM_EMBEDDING_DIMS", "1536"))
        use_in_memory = os.getenv("LANGMEM_USE_INMEMORY", "false").lower() == "true"

        _langmem_store_instance = LangMemStore(
            redis_url=redis_url,
            embedding_model=embedding_model,
            embedding_dims=embedding_dims,
            use_in_memory=use_in_memory
        )

        logger.info("✅ LangMemStore singleton created")

    return _langmem_store_instance
