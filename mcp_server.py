"""
Graphiti MCP Server for Neo4j AuraDB Integration

Provides memory search and storage endpoints for the Memory Router Proxy.
Connects to Neo4j AuraDB free instance.
"""
import os
from datetime import datetime
from typing import List, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Graphiti MCP Server",
    description="Memory storage for Proxy Orchestrator using Neo4j AuraDB",
    version="1.0.0"
)

# Initialize Neo4j driver for AuraDB
neo4j_uri = os.getenv("NEO4J_URI", "neo4j+s://your-instance.databases.neo4j.io")
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD")

if not neo4j_password:
    raise ValueError("NEO4J_PASSWORD must be set in .env file")

driver = GraphDatabase.driver(
    neo4j_uri,
    auth=(neo4j_user, neo4j_password)
)

# Initialize Graphiti (lazy import to handle optional dependency)
try:
    from graphiti_core import Graphiti
    from graphiti_core.nodes import EpisodeType
    
    graphiti = Graphiti(
        driver,
        llm_api_key=os.getenv("OPENAI_API_KEY")
    )
    GRAPHITI_AVAILABLE = True
except ImportError:
    print("WARNING: graphiti-core not installed. Using basic Neo4j storage.")
    GRAPHITI_AVAILABLE = False


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
            "neo4j_uri": neo4j_uri.split("@")[-1] if "@" in neo4j_uri else neo4j_uri,
            "graphiti": "available" if GRAPHITI_AVAILABLE else "unavailable",
            "mode": "graphiti" if GRAPHITI_AVAILABLE else "basic"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.post("/mcp/search", response_model=SearchResponse)
async def search_memories(request: SearchRequest):
    """
    Search for relevant memories.
    
    Uses Graphiti if available, otherwise falls back to basic Neo4j queries.
    """
    try:
        if GRAPHITI_AVAILABLE:
            # Use Graphiti's semantic search
            results = await graphiti.search(
                query=request.query,
                group_ids=[request.user_id],
                limit=request.limit
            )
            
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "content": result.get("content", ""),
                    "relevance": result.get("score", 0.0),
                    "timestamp": result.get("created_at", ""),
                    "metadata": result.get("metadata", {})
                })
        else:
            # Basic fallback using Neo4j direct queries
            with driver.session() as session:
                cypher_query = """
                MATCH (m:Memory {user_id: $user_id})
                WHERE m.content CONTAINS $query
                RETURN m.content as content, 
                       m.timestamp as timestamp,
                       m.metadata as metadata
                ORDER BY m.timestamp DESC
                LIMIT $limit
                """
                
                result = session.run(
                    cypher_query,
                    user_id=request.user_id,
                    query=request.query,
                    limit=request.limit
                )
                
                formatted_results = []
                for record in result:
                    formatted_results.append({
                        "content": record["content"],
                        "relevance": 0.8,  # Static score for basic mode
                        "timestamp": record["timestamp"],
                        "metadata": record.get("metadata", {})
                    })
        
        return SearchResponse(results=formatted_results)
        
    except Exception as e:
        print(f"Search error: {e}")
        # Graceful degradation - return empty results
        return SearchResponse(results=[])


@app.post("/mcp/store")
async def store_memory(request: StoreRequest):
    """
    Store new memory in Neo4j/Graphiti.
    """
    try:
        if GRAPHITI_AVAILABLE:
            # Use Graphiti for entity extraction and storage
            await graphiti.add_episode(
                name=f"memory_{datetime.now().isoformat()}",
                episode_body=request.content,
                episode_type=EpisodeType.message,
                group_id=request.user_id,
                metadata=request.metadata or {}
            )
        else:
            # Basic storage using Neo4j
            with driver.session() as session:
                cypher_query = """
                CREATE (m:Memory {
                    user_id: $user_id,
                    content: $content,
                    timestamp: $timestamp,
                    metadata: $metadata
                })
                RETURN m
                """
                
                session.run(
                    cypher_query,
                    user_id=request.user_id,
                    content=request.content,
                    timestamp=datetime.now().isoformat(),
                    metadata=request.metadata or {}
                )
        
        return {
            "success": True,
            "message": "Memory stored successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to store memory: {str(e)}"
        )


@app.get("/mcp/stats")
async def get_stats():
    """Get memory statistics"""
    try:
        with driver.session() as session:
            # Count total nodes
            result = session.run("MATCH (n) RETURN count(n) as total")
            total_nodes = result.single()["total"]
            
            # Count total relationships
            result = session.run("MATCH ()-[r]->() RETURN count(r) as total")
            total_relationships = result.single()["total"]
            
            # Count memories by user
            result = session.run("""
                MATCH (m)
                WHERE m.user_id IS NOT NULL
                RETURN m.user_id as user_id, count(m) as count
                ORDER BY count DESC
                LIMIT 10
            """)
            
            user_stats = [{"user_id": r["user_id"], "memories": r["count"]} 
                         for r in result]
            
            return {
                "total_nodes": total_nodes,
                "total_relationships": total_relationships,
                "users": user_stats,
                "mode": "graphiti" if GRAPHITI_AVAILABLE else "basic",
                "status": "operational"
            }
    except Exception as e:
        return {
            "error": str(e),
            "status": "error"
        }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("MCP_PORT", "5000"))
    print(f"Starting Graphiti MCP Server on port {port}")
    print(f"Neo4j URI: {neo4j_uri}")
    print(f"Mode: {'Graphiti' if GRAPHITI_AVAILABLE else 'Basic Neo4j'}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
