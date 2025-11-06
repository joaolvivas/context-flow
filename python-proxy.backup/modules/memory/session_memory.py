"""
Session Memory (Tier 2) - Fast Fact Extraction

Extracts key facts from conversations using a fast LLM and stores them in Redis.
Provides semantic search over recent facts without the overhead of full knowledge graph.
"""
import json
import redis
import openai
from typing import List, Dict, Optional
from datetime import datetime


class SessionMemory:
    """
    Extracts and stores session facts for fast retrieval.
    
    Benefits:
    - Fast extraction with gpt-4o-mini (~1-2s)
    - Simple key-value storage
    - 24-hour retention
    - Semantic search over recent facts
    """
    
    FACT_EXTRACTION_PROMPT = """Extract key facts from this conversation turn.
Focus on:
- Personal information (names, preferences, relationships)
- Important details (locations, dates, events)
- User statements and declarations

Return ONLY a JSON list of facts, each with 'category' and 'fact' fields.
Keep facts concise and specific.

Example output:
[
    {{"category": "pet", "fact": "User's dog is named Max"}},
    {{"category": "preference", "fact": "User's favorite color is black"}},
    {{"category": "team", "fact": "User supports Botafogo football club"}}
]

Conversation:
User: {user_message}
Assistant: {assistant_message}

Facts (JSON only):"""
    
    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 1,  # Different DB from working memory
        openai_api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        ttl_seconds: int = 86400  # 24 hours
    ):
        """
        Initialize session memory.
        
        Args:
            redis_host: Redis server host
            redis_port: Redis server port
            redis_db: Redis database number
            openai_api_key: OpenAI API key for fact extraction
            model: LLM model to use (fast model recommended)
            ttl_seconds: Time-to-live for facts
        """
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True
        )
        self.openai_api_key = openai_api_key
        self.model = model
        self.ttl_seconds = ttl_seconds
    
    def extract_facts(
        self,
        user_message: str,
        assistant_message: str
    ) -> List[Dict]:
        """
        Extract facts from a conversation turn using LLM.
        
        Args:
            user_message: User's message
            assistant_message: Assistant's response
        
        Returns:
            List of extracted facts
        """
        if not self.openai_api_key:
            return []
        
        try:
            prompt = self.FACT_EXTRACTION_PROMPT.format(
                user_message=user_message,
                assistant_message=assistant_message
            )
            
            client = openai.OpenAI(api_key=self.openai_api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON response
            # Handle markdown code blocks
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            facts = json.loads(content)
            
            # Validate structure
            if isinstance(facts, list):
                return [f for f in facts if "fact" in f]
            
            return []
            
        except Exception as e:
            print(f"Fact extraction error: {e}")
            return []
    
    def store_facts(
        self,
        user_id: str,
        conversation_id: str,
        facts: List[Dict]
    ) -> int:
        """
        Store extracted facts in Redis.
        
        Args:
            user_id: User identifier
            conversation_id: Conversation identifier
            facts: List of facts to store
        
        Returns:
            Number of facts stored
        """
        if not facts:
            return 0
        
        key = f"session_facts:{user_id}:{conversation_id}"
        
        # Get existing facts
        facts_json = self.redis_client.get(key)
        existing_facts = json.loads(facts_json) if facts_json else []
        
        # Add new facts with timestamp
        for fact in facts:
            existing_facts.append({
                **fact,
                "timestamp": datetime.now().isoformat()
            })
        
        # Store with TTL
        self.redis_client.setex(
            key,
            self.ttl_seconds,
            json.dumps(existing_facts)
        )
        
        return len(facts)
    
    def get_facts(
        self,
        user_id: str,
        conversation_id: str,
        category: Optional[str] = None
    ) -> List[Dict]:
        """
        Get stored facts for a conversation.
        
        Args:
            user_id: User identifier
            conversation_id: Conversation identifier
            category: Optional category filter
        
        Returns:
            List of facts
        """
        key = f"session_facts:{user_id}:{conversation_id}"
        facts_json = self.redis_client.get(key)
        
        if not facts_json:
            return []
        
        facts = json.loads(facts_json)
        
        if category:
            facts = [f for f in facts if f.get("category") == category]
        
        return facts
    
    def search_facts(
        self,
        user_id: str,
        conversation_id: str,
        query: str,
        limit: int = 5
    ) -> List[Dict]:
        """
        Simple text-based search over facts.
        
        Args:
            user_id: User identifier
            conversation_id: Conversation identifier
            query: Search query
            limit: Max results
        
        Returns:
            Matching facts
        """
        facts = self.get_facts(user_id, conversation_id)
        
        if not facts:
            return []
        
        # Simple keyword matching
        query_lower = query.lower()
        matches = []
        
        for fact in facts:
            fact_text = fact.get("fact", "").lower()
            category = fact.get("category", "").lower()
            
            # Score based on keyword overlap
            score = 0
            if query_lower in fact_text:
                score += 2
            if query_lower in category:
                score += 1
            
            # Check individual words
            for word in query_lower.split():
                if len(word) > 3:  # Skip short words
                    if word in fact_text:
                        score += 1
            
            if score > 0:
                matches.append({
                    **fact,
                    "relevance": score
                })
        
        # Sort by relevance
        matches.sort(key=lambda x: x["relevance"], reverse=True)
        
        return matches[:limit]
    
    def format_as_context(
        self,
        user_id: str,
        conversation_id: str,
        query: Optional[str] = None,
        limit: int = 5
    ) -> str:
        """
        Format facts as context string.
        
        Args:
            user_id: User identifier
            conversation_id: Conversation identifier
            query: Optional search query
            limit: Max facts to include
        
        Returns:
            Formatted context string
        """
        if query:
            facts = self.search_facts(user_id, conversation_id, query, limit)
        else:
            facts = self.get_facts(user_id, conversation_id)[-limit:]
        
        if not facts:
            return ""
        
        formatted = ["Recent facts about user:"]
        for fact in facts:
            formatted.append(f"  - {fact['fact']}")
        
        return "\n".join(formatted)
    
    def health_check(self) -> bool:
        """Check if Redis is available."""
        try:
            return self.redis_client.ping()
        except Exception:
            return False
