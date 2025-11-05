"""
Working Memory (Tier 1) - Recent Conversation Cache

Stores the last N conversation turns in Redis with a short TTL.
This provides instant context for ongoing conversations without
any processing or token costs.
"""
import json
import redis
from typing import List, Dict, Optional
from datetime import datetime


class WorkingMemory:
    """
    Stores and retrieves recent conversation turns from Redis.
    
    Benefits:
    - Instant retrieval (~1ms)
    - Zero token cost
    - No processing needed
    - Perfect for conversation continuity
    """
    
    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        max_turns: int = 20,
        ttl_seconds: int = 1800  # 30 minutes
    ):
        """
        Initialize working memory.
        
        Args:
            redis_host: Redis server host
            redis_port: Redis server port
            redis_db: Redis database number
            max_turns: Maximum conversation turns to keep
            ttl_seconds: Time-to-live for conversation cache
        """
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True
        )
        self.max_turns = max_turns
        self.ttl_seconds = ttl_seconds
    
    def add_turn(
        self,
        user_id: str,
        conversation_id: str,
        role: str,
        content: str
    ) -> None:
        """
        Add a conversation turn to working memory.
        
        Args:
            user_id: User identifier
            conversation_id: Conversation identifier
            role: Message role (user/assistant)
            content: Message content
        """
        key = f"working_memory:{user_id}:{conversation_id}"
        
        # Get existing turns
        turns_json = self.redis_client.get(key)
        turns = json.loads(turns_json) if turns_json else []
        
        # Add new turn
        turns.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last N turns (rolling window)
        if len(turns) > self.max_turns:
            turns = turns[-self.max_turns:]
        
        # Store back with TTL
        self.redis_client.setex(
            key,
            self.ttl_seconds,
            json.dumps(turns)
        )
    
    def get_recent_turns(
        self,
        user_id: str,
        conversation_id: str,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Get recent conversation turns.
        
        Args:
            user_id: User identifier
            conversation_id: Conversation identifier
            limit: Max turns to return (default: all)
        
        Returns:
            List of conversation turns
        """
        key = f"working_memory:{user_id}:{conversation_id}"
        turns_json = self.redis_client.get(key)
        
        if not turns_json:
            return []
        
        turns = json.loads(turns_json)
        
        if limit:
            return turns[-limit:]
        
        return turns
    
    def format_as_context(
        self,
        user_id: str,
        conversation_id: str,
        limit: Optional[int] = None
    ) -> str:
        """
        Format recent turns as context string.
        
        Args:
            user_id: User identifier
            conversation_id: Conversation identifier
            limit: Max turns to include
        
        Returns:
            Formatted context string
        """
        turns = self.get_recent_turns(user_id, conversation_id, limit)
        
        if not turns:
            return ""
        
        formatted = []
        for turn in turns:
            role = turn["role"].capitalize()
            content = turn["content"]
            formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)
    
    def clear_conversation(
        self,
        user_id: str,
        conversation_id: str
    ) -> None:
        """
        Clear a conversation from working memory.
        
        Args:
            user_id: User identifier
            conversation_id: Conversation identifier
        """
        key = f"working_memory:{user_id}:{conversation_id}"
        self.redis_client.delete(key)
    
    def health_check(self) -> bool:
        """Check if Redis is available."""
        try:
            return self.redis_client.ping()
        except Exception:
            return False
