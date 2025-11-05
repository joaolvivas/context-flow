# MCP/Graphiti Setup Guide

> How to set up Graphiti MCP server for memory storage

The Memory Router Proxy uses **Graphiti** (via MCP) for graph-based memory storage with Neo4j. This guide walks you through the complete setup.

## Why Graphiti?

**Graphiti** is a temporal knowledge graph library that:
- ✅ Automatically extracts entities and relationships from text
- ✅ Builds a knowledge graph of your conversations
- ✅ Provides semantic AND structural search
- ✅ Tracks how knowledge evolves over time
- ✅ Integrates with Neo4j for powerful graph queries

**Much more powerful than vector embeddings alone!**

## Prerequisites

1. **Python 3.9+**
2. **Neo4j Database**
   - Local installation OR
   - Docker container OR
   - Neo4j Aura (cloud)
3. **OpenAI API key** (for Graphiti's entity extraction)

## Quick Setup

### Option 1: Using Docker (Recommended)

**1. Start Neo4j with Docker:**

```bash
docker run -d \
  --name neo4j-memory \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your-password \
  -e NEO4J_PLUGINS='["apoc"]' \
  neo4j:latest
```

**2. Verify Neo4j is running:**

Open http://localhost:7474 in your browser
- Username: `neo4j`
- Password: `your-password`

**3. Install Graphiti:**

```bash
pip install graphiti-core neo4j
```

**4. Create MCP Server:**

Create `mcp_server.py`:

```python
"""
MCP Server for Graphiti Memory Storage
Provides search and store endpoints for the Memory Router Proxy
"""
import os
from datetime import datetime
from typing import List, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from neo4j import GraphDatabase
from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType

app = FastAPI(title="Graphiti MCP Server", version="1.0.0")

# Initialize Neo4j driver
neo4j_driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    auth=(
        os.getenv("NEO4J_USER", "neo4j"),
        os.getenv("NEO4J_PASSWORD", "your-password")
    )
)

# Initialize Graphiti
graphiti = Graphiti(
    neo4j_driver,
    llm_api_key=os.getenv("OPENAI_API_KEY")
)


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
        # Test Neo4j connection
        with neo4j_driver.session() as session:
            result = session.run("RETURN 1 as test")
            result.single()

        return {
            "status": "healthy",
            "neo4j": "connected",
            "graphiti": "initialized"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.post("/mcp/search", response_model=SearchResponse)
async def search_memories(request: SearchRequest):
    """
    Search for relevant memories using Graphiti

    Args:
        query: Search query text
        user_id: User namespace for isolation
        limit: Maximum results to return

    Returns:
        List of relevant memory chunks with relevance scores
    """
    try:
        # Search using Graphiti
        results = await graphiti.search(
            query=request.query,
            group_ids=[request.user_id],  # User isolation
            limit=request.limit
        )

        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                "content": result.get("content", ""),
                "relevance": result.get("score", 0.0),
                "timestamp": result.get("created_at", ""),
                "metadata": result.get("metadata", {})
            })

        return SearchResponse(results=formatted_results)

    except Exception as e:
        # Graceful degradation - return empty results
        return SearchResponse(results=[])


@app.post("/mcp/store")
async def store_memory(request: StoreRequest):
    """
    Store new memory in Graphiti

    Args:
        content: Memory content to store
        user_id: User namespace
        metadata: Optional metadata (timestamp, conversation_id, etc)

    Returns:
        Success confirmation
    """
    try:
        # Store in Graphiti
        await graphiti.add_episode(
            name=f"memory_{datetime.now().isoformat()}",
            episode_body=request.content,
            episode_type=EpisodeType.message,
            group_id=request.user_id,  # User isolation
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
        with neo4j_driver.session() as session:
            # Count total nodes
            result = session.run("MATCH (n) RETURN count(n) as total")
            total_nodes = result.single()["total"]

            # Count total relationships
            result = session.run("MATCH ()-[r]->() RETURN count(r) as total")
            total_relationships = result.single()["total"]

            return {
                "total_nodes": total_nodes,
                "total_relationships": total_relationships,
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
    print(f"Neo4j URI: {os.getenv('NEO4J_URI', 'bolt://localhost:7687')}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
```

**5. Create `.env` for MCP Server:**

```bash
# MCP Server Configuration
MCP_PORT=5000

# Neo4j Connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# OpenAI for Graphiti (entity extraction)
OPENAI_API_KEY=sk-your-key-here
```

**6. Start MCP Server:**

```bash
python mcp_server.py
```

You should see:
```
Starting Graphiti MCP Server on port 5000
INFO:     Uvicorn running on http://0.0.0.0:5000
```

**7. Test MCP Server:**

```bash
# Health check
curl http://localhost:5000/health

# Test store
curl -X POST http://localhost:5000/mcp/store \
  -H "Content-Type: application/json" \
  -d '{
    "content": "The user likes Python programming",
    "user_id": "test_user",
    "metadata": {"timestamp": "2024-01-15T10:00:00"}
  }'

# Test search
curl -X POST http://localhost:5000/mcp/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What programming language?",
    "user_id": "test_user",
    "limit": 5
  }'
```

**8. Update Memory Router Proxy `.env`:**

```bash
# In .env
MCP_SEARCH_ENDPOINT=http://localhost:5000/mcp/search
MCP_STORE_ENDPOINT=http://localhost:5000/mcp/store
```

**Done!** Your Memory Router Proxy now has graph-based memory! 🎉

### Option 2: Local Neo4j Installation

**1. Install Neo4j:**

Download from https://neo4j.com/download/

**2. Start Neo4j:**

```bash
neo4j start
```

**3. Set up password:**

```bash
neo4j-admin set-initial-password your-password
```

**4. Follow steps 3-8 from Option 1 above**

### Option 3: Neo4j Aura (Cloud)

**1. Create free account:**

Go to https://console.neo4j.io/

**2. Create database:**

- Select "Create Free Database"
- Copy connection URI (e.g., `neo4j+s://xxxxx.databases.neo4j.io`)
- Copy password

**3. Update MCP `.env`:**

```bash
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-generated-password
```

**4. Follow steps 3-8 from Option 1 above**

## Verifying the Setup

### 1. Check Neo4j Browser

Open http://localhost:7474 and run:

```cypher
// See all nodes
MATCH (n) RETURN n LIMIT 25

// See memory episodes
MATCH (e:Episode) RETURN e

// See extracted entities
MATCH (entity) WHERE entity:Entity RETURN entity

// See relationships
MATCH (a)-[r]->(b) RETURN a, r, b LIMIT 25
```

### 2. Check MCP Stats

```bash
curl http://localhost:5000/mcp/stats
```

Should show:
```json
{
  "total_nodes": 150,
  "total_relationships": 87,
  "status": "operational"
}
```

### 3. Test End-to-End

```python
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_OPENAI_KEY",
    base_url="http://localhost:8000/v1",
    default_headers={"X-User-Id": "test_user"}
)

# First conversation
response1 = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "I love building AI agents with Python"}]
)

# Later conversation - should remember
response2 = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What do I like to build?"}]
)

print(response2.choices[0].message.content)
# Should mention Python, AI agents, etc.
```

## Advanced: Graphiti Features

### Custom Entity Types

Extend Graphiti to extract custom entities:

```python
from graphiti_core.nodes import EntityType

# Define custom entity types
class ProjectEntity(EntityType):
    name = "Project"
    description = "Software projects the user is working on"

# Register with Graphiti
graphiti.register_entity_type(ProjectEntity)
```

### Temporal Queries

Query how knowledge evolved over time:

```python
# Find what changed about a topic
results = await graphiti.search_temporal(
    query="Python knowledge",
    user_id="alice",
    start_date="2024-01-01",
    end_date="2024-12-31"
)
```

### Graph Queries

Direct Neo4j queries for complex relationships:

```python
with neo4j_driver.session() as session:
    # Find all entities related to a topic
    result = session.run("""
        MATCH (e:Entity)-[r:RELATES_TO]->(topic:Entity {name: 'Python'})
        RETURN e, r, topic
    """)
```

## Troubleshooting

### MCP Server Won't Start

**Error: "Cannot connect to Neo4j"**

Check Neo4j is running:
```bash
# Docker
docker ps | grep neo4j

# Local
neo4j status
```

Check connection details in `.env`:
```bash
NEO4J_URI=bolt://localhost:7687  # Correct protocol?
NEO4J_PASSWORD=your-password     # Correct password?
```

### Memory Not Being Stored

**Check MCP logs:**
```bash
# Should see POST requests to /mcp/store
python mcp_server.py
```

**Check Neo4j:**
```cypher
MATCH (n) RETURN count(n)
// Should see nodes being created
```

### Search Returns No Results

**Check if data exists:**
```bash
curl http://localhost:5000/mcp/stats
```

**Check Graphiti indexing:**

Graphiti needs time to process and index. Wait a few seconds after storing, then search.

### High Latency

**Graphiti processing is async.** First store might be slow (entity extraction), but subsequent searches are fast.

**Optimize Neo4j:**
```cypher
// Create indexes
CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)
CREATE INDEX episode_timestamp IF NOT EXISTS FOR (e:Episode) ON (e.created_at)
```

## Production Considerations

### 1. Scale Neo4j

For production, use:
- **Neo4j Enterprise** for clustering
- **Neo4j Aura Professional** for managed service
- **Dedicated server** with SSD storage

### 2. Monitor Memory Usage

```bash
# Neo4j memory usage
docker stats neo4j-memory

# Or check Neo4j browser: :sysinfo
```

### 3. Backup Strategy

```bash
# Docker backup
docker exec neo4j-memory neo4j-admin dump --to=/backups/backup.dump

# Copy backup out
docker cp neo4j-memory:/backups/backup.dump ./backup.dump
```

### 4. Security

- Use **strong Neo4j password**
- Enable **SSL/TLS** for production
- Restrict **network access** to Neo4j port (7687)
- Use **firewall rules**

## Alternative: Without Graphiti

You can use the Memory Router Proxy without MCP/Graphiti:

**In `.env`:**
```bash
MEMORY_ENABLED=false
```

The proxy will work as a transparent pass-through without memory features.

**Or implement your own MCP endpoints:**

The proxy just expects:
- `POST /mcp/search` - Returns relevant memories
- `POST /mcp/store` - Stores new memories

You can implement these with any backend (PostgreSQL, Redis, etc.)

## Need Help?

- **Graphiti Docs**: https://github.com/getzep/graphiti-core
- **Neo4j Docs**: https://neo4j.com/docs/
- **MCP Specification**: https://modelcontextprotocol.io/

---

**You now have a complete graph-based memory system!** 🧠🚀
