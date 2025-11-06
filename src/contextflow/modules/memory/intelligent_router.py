"""
Intelligent Memory Router

Decides which memory tier(s) to query based on the query type and context.
Combines results from multiple tiers efficiently.
"""
import re
from typing import List, Dict, Tuple, Optional
from contextflow.modules.memory.working_memory import WorkingMemory
from contextflow.modules.memory.session_memory import SessionMemory


class MemoryRouter:
    """
    Routes queries to appropriate memory tiers and combines results.
    
    Query Routing Strategy:
    - Tier 1 (Working Memory): Always included for conversation continuity
    - Tier 2 (Session Facts): For factual/personal queries
    - Tier 3 (Graphiti): For complex/historical queries only
    """
    
    # Patterns that suggest deep/historical queries (2% of queries)
    # Supports English and Portuguese
    DEEP_QUERY_PATTERNS = [
        # English patterns
        r'\b(remember|recall|previous|earlier|before|history|past)\b',
        r'\b(when did|how long|since when|relationship|connection)\b',
        r'\b(compare|difference|similar|related to|evolution|timeline)\b',
        r'\b(all my|every time|throughout|over time|everything)\b',
        r'\b(background|experience|career|professional|work history)\b',
        # Portuguese patterns
        r'\b(lembr|record|anterior|antes|história|passado)\b',
        r'\b(quando|quanto tempo|desde quando|relacionamento|conexão)\b',
        r'\b(compar|diferença|similar|relacionado|evolução|linha do tempo)\b',
        r'\b(tod[oa]s? (minhas?|meus?|a informação)|sempre|ao longo)\b',
        r'\b(background|experiência|carreira|profissional|histórico|trajetória)\b',
        r'\b(me conte|me fale|traga|busque).{0,30}(tudo|toda|informação)\b',
    ]

    # Patterns for factual queries (8% of queries)
    # Supports English and Portuguese
    FACTUAL_QUERY_PATTERNS = [
        # English patterns
        r'\b(what is|what\'s|who is|where is|name|favorite|prefer)\b',
        r'\b(my .{1,20}\?|tell me about|information about)\b',
        r'\b(list|show|display) (my|all)\b',
        # Portuguese patterns
        r'\b(o que é|qual é|quem é|onde é|nome|favorito|prefiro|prefer)\b',
        r'\b(me fale sobre|informação sobre|me conte sobre|sobre mim)\b',
        r'\b(list|mostr|exib)[ea]r? (meu|minha|todo|toda)\b',
    ]
    
    def __init__(
        self,
        working_memory: WorkingMemory,
        session_memory: SessionMemory,
        graphiti_enabled: bool = True
    ):
        """
        Initialize memory router.
        
        Args:
            working_memory: Working memory instance (Tier 1)
            session_memory: Session memory instance (Tier 2)
            graphiti_enabled: Whether to use Graphiti (Tier 3)
        """
        self.working_memory = working_memory
        self.session_memory = session_memory
        self.graphiti_enabled = graphiti_enabled
    
    def classify_query(self, query: str) -> Dict[str, any]:
        """
        Classify query to determine which tiers to use.
        
        Progressive Injection Strategy:
        - Tier 1 only (90%): Simple queries, greetings, continuations
        - Tier 1 + 2 (8%): Factual queries about user info
        - All tiers (2%): Deep/historical/analytical queries
        
        Args:
            query: User query
        
        Returns:
            Dict with tier activation flags and query type
        """
        query_lower = query.lower()
        query_length = len(query.split())
        
        # Check for deep/historical query patterns
        is_deep_query = any(
            re.search(pattern, query_lower, re.IGNORECASE)
            for pattern in self.DEEP_QUERY_PATTERNS
        )
        
        # Check for factual query patterns
        is_factual = any(
            re.search(pattern, query_lower, re.IGNORECASE)
            for pattern in self.FACTUAL_QUERY_PATTERNS
        )
        
        # Determine query tier level
        if is_deep_query:
            tier_level = 3  # All tiers
            use_working_memory = True
            use_session_facts = True
            use_graphiti = self.graphiti_enabled
        elif is_factual or query_length < 8:  # Very short queries often factual
            tier_level = 2  # Tier 1 + 2
            use_working_memory = True
            use_session_facts = True
            use_graphiti = False
        else:
            tier_level = 1  # Tier 1 only
            use_working_memory = True
            use_session_facts = False
            use_graphiti = False
        
        return {
            "use_working_memory": use_working_memory,
            "use_session_facts": use_session_facts,
            "use_graphiti": use_graphiti,
            "tier_level": tier_level,
            "is_deep_query": is_deep_query,
            "is_factual": is_factual
        }
    
    def get_memory_context(
        self,
        user_id: str,
        conversation_id: str,
        query: str,
        graphiti_search_func: Optional[callable] = None
    ) -> Tuple[str, Dict]:
        """
        Get combined memory context from appropriate tiers.
        
        Args:
            user_id: User identifier
            conversation_id: Conversation identifier
            query: User query
            graphiti_search_func: Optional function to search Graphiti (Tier 3)
        
        Returns:
            Tuple of (formatted_context, metadata)
        """
        classification = self.classify_query(query)
        
        context_parts = []
        metadata = {
            "tiers_used": [],
            "working_memory_turns": 0,
            "session_facts": 0,
            "graphiti_memories": 0,
            "total_cost_estimate": 0  # Token cost estimate
        }
        
        # Progressive injection based on tier level
        tier_level = classification.get("tier_level", 1)
        
        # Tier 1: Working Memory (Always, but variable depth)
        if classification["use_working_memory"]:
            # Use fewer turns for simple queries (token optimization)
            turn_limit = 10 if tier_level == 1 else 15 if tier_level == 2 else 20
            
            working_context = self.working_memory.format_as_context(
                user_id, conversation_id, limit=turn_limit
            )
            if working_context:
                context_parts.append(f"<recent_conversation>\n{working_context}\n</recent_conversation>")
                turns = self.working_memory.get_recent_turns(user_id, conversation_id, limit=turn_limit)
                metadata["working_memory_turns"] = len(turns)
                metadata["tiers_used"].append("working_memory")
                # Estimate: ~20 tokens per turn
                metadata["total_cost_estimate"] += len(turns) * 20
        
        # Tier 2: Session Facts
        if classification["use_session_facts"]:
            session_context = self.session_memory.format_as_context(
                user_id, conversation_id, query=query, limit=5
            )
            if session_context:
                context_parts.append(f"<user_facts>\n{session_context}\n</user_facts>")
                facts = self.session_memory.search_facts(user_id, conversation_id, query, limit=5)
                metadata["session_facts"] = len(facts)
                metadata["tiers_used"].append("session_facts")
                # Estimate: ~100 tokens for facts
                metadata["total_cost_estimate"] += 100
        
        # Tier 3: Graphiti (Only for deep queries)
        if classification["use_graphiti"] and graphiti_search_func:
            try:
                graphiti_results = graphiti_search_func(query, user_id, limit=10)
                if graphiti_results:
                    formatted_graphiti = self._format_graphiti_results(graphiti_results)
                    context_parts.append(f"<knowledge_graph>\n{formatted_graphiti}\n</knowledge_graph>")
                    metadata["graphiti_memories"] = len(graphiti_results)
                    metadata["tiers_used"].append("graphiti")
                    # Estimate: ~500 tokens for graph context
                    metadata["total_cost_estimate"] += 500
            except Exception as e:
                print(f"Graphiti search error: {e}")
        
        # Combine all context
        combined_context = "\n\n".join(context_parts) if context_parts else ""
        
        return combined_context, metadata
    
    def store_conversation_turn(
        self,
        user_id: str,
        conversation_id: str,
        user_message: str,
        assistant_response: str,
        extract_facts: bool = True
    ) -> Dict:
        """
        Store conversation turn across appropriate tiers.
        
        Args:
            user_id: User identifier
            conversation_id: Conversation identifier
            user_message: User's message
            assistant_response: Assistant's response
            extract_facts: Whether to extract facts (Tier 2)
        
        Returns:
            Storage metadata
        """
        metadata = {
            "working_memory_stored": False,
            "session_facts_extracted": 0,
            "graphiti_queued": False
        }
        
        # Tier 1: Always store in working memory
        try:
            self.working_memory.add_turn(user_id, conversation_id, "user", user_message)
            self.working_memory.add_turn(user_id, conversation_id, "assistant", assistant_response)
            metadata["working_memory_stored"] = True
        except Exception as e:
            print(f"Working memory storage error: {e}")
        
        # Tier 2: Extract and store facts (async)
        if extract_facts:
            try:
                facts = self.session_memory.extract_facts(user_message, assistant_response)
                if facts:
                    count = self.session_memory.store_facts(user_id, conversation_id, facts)
                    metadata["session_facts_extracted"] = count
            except Exception as e:
                print(f"Session memory extraction error: {e}")
        
        # Tier 3: Graphiti storage happens in background queue (handled separately)
        metadata["graphiti_queued"] = True
        
        return metadata
    
    def _format_graphiti_results(self, results: List[Dict]) -> str:
        """Format Graphiti results for context injection."""
        formatted = []
        for idx, result in enumerate(results, 1):
            content = result.get("content", "")
            formatted.append(f"{idx}. {content}")
        return "\n".join(formatted)
    
    def get_stats(self) -> Dict:
        """Get memory system statistics."""
        return {
            "working_memory_healthy": self.working_memory.health_check(),
            "session_memory_healthy": self.session_memory.health_check(),
            "graphiti_enabled": self.graphiti_enabled
        }
