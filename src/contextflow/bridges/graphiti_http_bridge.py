#!/usr/bin/env python3
"""
HTTP Bridge for Graphiti MCP Server

Bridges the Proxy Orchestrator (which expects HTTP endpoints) with your 
existing Graphiti MCP server (which uses stdio/MCP protocol).

This creates HTTP endpoints at:
- POST /mcp/search - Search memories
- POST /mcp/store - Store memories  
- GET /health - Health check
- GET /mcp/stats - Statistics

Your existing MCP server at /Users/joaolucas/graphiti/mcp_server/ is used directly.
"""
import os
import asyncio
from datetime import datetime
from typing import List, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Direct import of Graphiti
from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType

# Load environment from your existing MCP server directory
load_dotenv("/Users/joaolucas/graphiti/mcp_server/.env")

app = FastAPI(
    title="Graphiti HTTP Bridge",
    description="HTTP endpoints for Proxy Orchestrator → Graphiti MCP",
    version="1.0.0"
)

# Use your existing Neo4j AuraDB credentials
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j+s://81a320df.databases.neo4j.io")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROUP_ID = os.getenv("GROUP_ID", "lucas-ai")

if not NEO4J_PASSWORD:
    raise ValueError("NEO4J_PASSWORD not found in environment")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment")

# Initialize Neo4j driver
driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
)

# Initialize Graphiti with proper configuration
from graphiti_core.llm_client import OpenAIClient
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.embedder import OpenAIEmbedder, OpenAIEmbedderConfig


class PatchedOpenAIClient(OpenAIClient):
    """Drop unsupported reasoning payloads before hitting OpenAI."""

    async def _create_structured_completion(
        self,
        model,
        messages,
        temperature,
        max_tokens,
        response_model,
        **kwargs,
    ):
        """Match the parent implementation while ignoring unsupported kwargs (e.g. reasoning)."""
        return await self.client.beta.chat.completions.parse(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_model,  # type: ignore[arg-type]
        )

# Create LLM config - use standard model to avoid reasoning parameter
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
llm_config = LLMConfig(
    api_key=OPENAI_API_KEY,
    model="gpt-4o",  # gpt-4o supports all parameters
    temperature=0.0
)
llm_client = PatchedOpenAIClient(config=llm_config)

# Create embedder config
embedder_config = OpenAIEmbedderConfig(
    api_key=OPENAI_API_KEY,
    model="text-embedding-3-small"
)
embedder = OpenAIEmbedder(config=embedder_config)

# Initialize Graphiti
graphiti_client = Graphiti(
    uri=NEO4J_URI,
    user=NEO4J_USER,
    password=NEO4J_PASSWORD,
    llm_client=llm_client,
    embedder=embedder
)

print(f"✓ Connected to Neo4j AuraDB: {NEO4J_URI}")
print(f"✓ Using group_id: {GROUP_ID}")


class SearchRequest(BaseModel):
    query: str
    user_id: str
    limit: int = 5


class StoreRequest(BaseModel):
    content: str
    user_id: str
    metadata: Optional[Dict] = None


class SearchResponse(BaseModel):
    results: List[Dict]


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            result.single()

        return {
            "status": "healthy",
            "neo4j": "connected",
            "neo4j_uri": NEO4J_URI,
            "group_id": GROUP_ID,
            "graphiti": "initialized",
            "mode": "bridge"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.post("/mcp/search", response_model=SearchResponse)
async def search_memories(request: SearchRequest):
    """
    Search for relevant memories using Graphiti.
    
    Uses the existing Graphiti instance with your AuraDB connection.
    """
    try:
        # Use Graphiti's search with the configured group_id
        results = await graphiti_client.search(
            query=request.query,
            group_ids=[GROUP_ID],  # Use your configured group_id
            num_results=request.limit
        )
        
        # Format results for Proxy Orchestrator
        formatted_results = []
        for result in results:
            formatted_results.append({
                "content": result.fact if hasattr(result, 'fact') else str(result),
                "relevance": result.search_score if hasattr(result, 'search_score') else 0.8,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "uuid": result.uuid if hasattr(result, 'uuid') else None,
                    "group_id": GROUP_ID
                }
            })
        
        return SearchResponse(results=formatted_results)
        
    except Exception as e:
        print(f"Search error: {e}")
        # Graceful degradation - return empty results
        return SearchResponse(results=[])


@app.post("/mcp/store")
async def store_memory(request: StoreRequest):
    """
    Store new memory in Graphiti.
    
    Creates an episode in your Graphiti knowledge graph.
    """
    try:
        # Store using Graphiti with your group_id
        await graphiti_client.add_episode(
            name=f"memory_{datetime.now().isoformat()}",
            episode_body=request.content,
            source_description="Memory from Proxy Orchestrator",
            reference_time=datetime.now(),
            source=EpisodeType.message,
            group_id=GROUP_ID
        )
        
        return {
            "success": True,
            "message": "Memory stored successfully in Graphiti",
            "group_id": GROUP_ID
        }
        
    except Exception as e:
        print(f"Store error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to store memory: {str(e)}"
        )


@app.get("/mcp/stats")
async def get_stats():
    """Get memory statistics from Neo4j"""
    try:
        with driver.session() as session:
            # Count total nodes
            result = session.run("MATCH (n) RETURN count(n) as total")
            total_nodes = result.single()["total"]
            
            # Count total relationships
            result = session.run("MATCH ()-[r]->() RETURN count(r) as total")
            total_relationships = result.single()["total"]
            
            # Count episodes for this group
            result = session.run("""
                MATCH (e:EpisodicNode)
                WHERE e.group_id = $group_id
                RETURN count(e) as episodes
            """, group_id=GROUP_ID)
            episodes = result.single()["episodes"] if result.peek() else 0
            
            return {
                "total_nodes": total_nodes,
                "total_relationships": total_relationships,
                "episodes": episodes,
                "group_id": GROUP_ID,
                "status": "operational",
                "mode": "graphiti_bridge"
            }
    except Exception as e:
        return {
            "error": str(e),
            "status": "error"
        }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("MCP_PORT", "5000"))
    print(f"\n🚀 Starting Graphiti HTTP Bridge on port {port}")
    print(f"📍 Neo4j: {NEO4J_URI}")
    print(f"👤 Group: {GROUP_ID}")
    print(f"\nEndpoints:")
    print(f"  - http://localhost:{port}/health")
    print(f"  - http://localhost:{port}/mcp/search")
    print(f"  - http://localhost:{port}/mcp/store")
    print(f"  - http://localhost:{port}/mcp/stats\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
