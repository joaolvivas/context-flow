"""
Intelligent Memory Router

Decides which memory tier(s) to query based on the query type and context.
Combines results from multiple tiers efficiently.
"""
import os
import re
from typing import List, Dict, Tuple, Optional
from modules.memory.working_memory import WorkingMemory
from modules.memory.session_memory import SessionMemory


class MemoryRouter:
    """
    Routes queries to appropriate memory tiers and combines results.
    
    Query Routing Strategy:
    - Tier 1 (Working Memory): Always included for conversation continuity
    - Tier 2 (Session Facts): For factual/personal queries
    - Tier 3 (Graphiti): For complex/historical queries only
    """
    
    # Patterns for COMPREHENSIVE queries (highest priority)
    # User wants EVERYTHING - requires query expansion + high limit
    COMPREHENSIVE_QUERY_PATTERNS = [
        # English patterns
        r'\b(tell me everything|everything about|all about|complete|comprehensive)\b',
        r'\b(what do you know about|what.{0,30}know.{0,30}(me|about me))\b',
        r'\b(my entire|my complete|my full).{0,30}(background|history|profile)\b',
        # Portuguese patterns
        r'\b(me conte tudo|tudo sobre|tudo que|toda informação)\b',
        r'\b(o que (você |voce )?sabe sobre|quem sou eu)\b',
        r'\b(meu completo|minha completa|todo meu).{0,30}(background|histórico|perfil)\b',
        r'\b(resumo (completo|detalhado|profissional))\b',
    ]

    # Patterns that suggest deep/historical queries (2% of queries)
    # Supports English and Portuguese
    DEEP_QUERY_PATTERNS = [
        # English patterns
        r'\b(remember|recall|previous|earlier|before|history|past)\b',
        r'\b(when did|how long|since when|relationship|connection)\b',
        r'\b(compare|difference|similar|related to|evolution|timeline)\b',
        r'\b(all my|every time|throughout|over time)\b',
        r'\b(background|experience|career|professional|work history)\b',
        # Portuguese patterns
        r'\b(lembr|record|anterior|antes|história|passado)\b',
        r'\b(quando|quanto tempo|desde quando|relacionamento|conexão)\b',
        r'\b(compar|diferença|similar|relacionado|evolução|linha do tempo)\b',
        r'\b(sempre|ao longo)\b',
        r'\b(background|experiência|carreira|profissional|histórico|trajetória)\b',
    ]

    # Patterns for factual queries (8% of queries)
    # Supports English and Portuguese
    FACTUAL_QUERY_PATTERNS = [
        # English patterns
        r'\b(what is|what\'s|who is|where is|name|favorite|prefer)\b',
        r'\b(my .{1,20}\?|tell me about|information about)\b',
        r'\b(list|show|display) (my|all)\b',
        # Portuguese patterns
        r'\b(o que é|qual é|quais|quem é|onde é|nome|favorito|prefiro|prefer)\b',
        r'\b(favorit[oa]?|cor favorita|time|time de coração|time do coração|cor)\b',
        r'\b(me fale sobre|informação sobre|me conte sobre|sobre mim|que tipo|que tipos|com quais)\b',
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
    
    def classify_query(self, query: str, force_graphiti: bool = False) -> Dict[str, any]:
        """
        Classify query to determine which tiers to use.

        Progressive Injection Strategy:
        - Tier 1 only (90%): Simple queries, greetings, continuations
        - Tier 1 + 2 (8%): Factual queries about user info
        - All tiers deep (1.5%): Deep/historical/analytical queries
        - All tiers comprehensive (0.5%): "Tell me everything" queries with expansion

        Args:
            query: User query

        Returns:
            Dict with tier activation flags and query type
        """
        query_lower = query.lower()
        query_length = len(query.split())

        # Check for comprehensive queries (HIGHEST PRIORITY)
        is_comprehensive = any(
            re.search(pattern, query_lower, re.IGNORECASE)
            for pattern in self.COMPREHENSIVE_QUERY_PATTERNS
        )

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
        # Allowed intents for Graphiti via env (comma-separated): deep,comprehensive,factual
        allowed_graphiti_intents = set(
            (os.getenv("GRAPHITI_ALLOWED_INTENTS", "deep,comprehensive,factual").lower())
            .replace(" ", "")
            .split(",")
        )

        why_tier3 = None
        if is_comprehensive:
            tier_level = 4  # COMPREHENSIVE - All tiers + query expansion + high limit
            use_working_memory = True
            use_session_facts = True
            use_graphiti = self.graphiti_enabled and ("comprehensive" in allowed_graphiti_intents)
            search_limit = 20  # High limit for comprehensive queries
            if use_graphiti:
                why_tier3 = "comprehensive_query"
        elif is_deep_query:
            tier_level = 3  # DEEP - All tiers
            use_working_memory = True
            use_session_facts = True
            use_graphiti = self.graphiti_enabled and ("deep" in allowed_graphiti_intents)
            search_limit = 10  # Medium limit
            if use_graphiti:
                why_tier3 = "deep_query_patterns"
        elif is_factual or query_length < 8:  # Very short queries often factual
            tier_level = 2  # FACTUAL - Tier 1 + 2 (+3 if allowed)
            use_working_memory = True
            use_session_facts = True
            use_graphiti = self.graphiti_enabled and ("factual" in allowed_graphiti_intents)
            search_limit = 5  # Standard limit
            if use_graphiti:
                why_tier3 = "factual_allowed_by_env"
        else:
            tier_level = 1  # SIMPLE - Tier 1 only
            use_working_memory = True
            use_session_facts = False
            use_graphiti = False
            search_limit = 0  # No Tier 3

        if force_graphiti:
            use_graphiti = self.graphiti_enabled
            use_session_facts = True
            why_tier3 = "forced"
            tier_level = max(tier_level, 3)

        return {
            "use_working_memory": use_working_memory,
            "use_session_facts": use_session_facts,
            "use_graphiti": use_graphiti,
            "tier_level": tier_level,
            "is_comprehensive": is_comprehensive,
            "is_deep_query": is_deep_query,
            "is_factual": is_factual,
            "search_limit": search_limit,
            "force_graphiti": force_graphiti,
            "why_tier3": why_tier3
        }
    
    def expand_comprehensive_query(self, query: str) -> List[str]:
        """
        Expand comprehensive queries into multiple targeted search terms.

        When user asks "tell me everything about me", we search for:
        - goals (short-term, long-term)
        - professional background
        - projects
        - achievements
        - preferences
        - etc.

        Args:
            query: Original user query

        Returns:
            List of expanded search terms
        """
        # Detect language
        is_portuguese = any(word in query.lower() for word in ['quem', 'sou', 'conte', 'tudo', 'sobre', 'meu', 'minha'])

        if is_portuguese:
            # Portuguese expansion terms
            return [
                "objetivos metas curto prazo longo prazo",
                "background profissional carreira trabalho",
                "projetos realizações conquistas",
                "experiência histórico trajetória",
                "preferências interesses hobbies",
                "equipe time pessoas relacionamentos",
                "ferramentas tecnologias skills",
                "educação formação aprendizado"
            ]
        else:
            # English expansion terms
            return [
                "goals objectives short-term long-term",
                "professional background career work",
                "projects achievements accomplishments",
                "experience history trajectory",
                "preferences interests hobbies",
                "team people relationships",
                "tools technologies skills",
                "education learning training"
            ]

    def get_memory_context(
        self,
        user_id: str,
        conversation_id: str,
        query: str,
        graphiti_search_func: Optional[callable] = None,
        force_graphiti: bool = False
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
        classification = self.classify_query(query, force_graphiti=force_graphiti)
        
        context_parts = []
        metadata = {
            "tiers_used": [],
            "working_memory_turns": 0,
            "session_facts": 0,
            "graphiti_memories": 0,
            "total_cost_estimate": 0,  # Token cost estimate
            "force_graphiti": classification.get("force_graphiti", False)
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
        
        # Tier 3: Graphiti (gated by intent and env)
        if classification["use_graphiti"] and graphiti_search_func:
            try:
                search_limit = classification.get("search_limit", 5)
                is_comprehensive = classification.get("is_comprehensive", False)

                # For comprehensive queries, use query expansion
                if is_comprehensive:
                    expanded_terms = self.expand_comprehensive_query(query)
                    all_results = []
                    seen_content = set()  # Deduplicate results

                    # Search with each expanded term
                    for term in expanded_terms:
                        results = graphiti_search_func(term, user_id, limit=3)
                        for result in results:
                            content = result.get("content", "")
                            if content and content not in seen_content:
                                all_results.append(result)
                                seen_content.add(content)

                    graphiti_results = all_results[:search_limit]  # Cap at search_limit
                else:
                    # Standard single query search
                    graphiti_results = graphiti_search_func(query, user_id, limit=search_limit)

                if graphiti_results:
                    formatted_graphiti = self._format_graphiti_results(graphiti_results)
                    context_parts.append(f"<knowledge_graph>\n{formatted_graphiti}\n</knowledge_graph>")
                    metadata["graphiti_memories"] = len(graphiti_results)
                    metadata["tiers_used"].append("graphiti")
                    # Why Tier 3
                    metadata["why_tier3"] = (
                        classification.get("is_comprehensive") and "comprehensive_query"
                    ) or (
                        classification.get("is_deep_query") and "deep_query_patterns"
                    ) or (
                        classification.get("is_factual") and "factual_allowed_by_env"
                    )
                    # Estimate: ~500 tokens base + 100 per additional result
                    metadata["total_cost_estimate"] += 500 + (len(graphiti_results) * 100)
            except Exception as e:
                print(f"Graphiti search error: {e}")

        if classification.get("why_tier3") and "why_tier3" not in metadata:
            metadata["why_tier3"] = classification.get("why_tier3")
        
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
