"""
Simple configuration for Memory Router Proxy
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Configuration loaded from .env file"""

    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="info", env="LOG_LEVEL")

    # LLM Provider (default - can be overridden per request)
    default_provider_url: str = Field(
        default="https://api.openai.com/v1",
        env="DEFAULT_PROVIDER_URL"
    )
    default_model: str = Field(
        default="gpt-4o-mini",
        env="DEFAULT_MODEL"
    )

    # MCP/Graphiti
    mcp_search_endpoint: str = Field(
        default="http://localhost:5000/mcp/search",
        env="MCP_SEARCH_ENDPOINT"
    )
    mcp_store_endpoint: str = Field(
        default="http://localhost:5000/mcp/store",
        env="MCP_STORE_ENDPOINT"
    )

    # Memory Settings
    memory_enabled: bool = Field(default=True, env="MEMORY_ENABLED")
    memory_search_limit: int = Field(default=5, env="MEMORY_SEARCH_LIMIT")
    memory_chunk_size: int = Field(default=500, env="MEMORY_CHUNK_SIZE")
    memory_max_context_tokens: int = Field(default=2000, env="MEMORY_MAX_CONTEXT_TOKENS")

    # Memory Backend Selection
    memory_backend: str = Field(
        default="graphiti",
        env="MEMORY_BACKEND",
        description="Backend type: 'graphiti' or 'supermemory'"
    )

    # Supermemory Configuration (when backend=supermemory)
    supermemory_base_url: str = Field(
        default="https://api.supermemory.ai",
        env="SUPERMEMORY_BASE_URL",
        description="Supermemory API URL (cloud or self-hosted)"
    )
    supermemory_api_key: Optional[str] = Field(
        default=None,
        env="SUPERMEMORY_API_KEY",
        description="API key for Supermemory cloud (not needed for self-hosted)"
    )

    # Conversational Cache Settings
    cache_enabled: bool = Field(default=True, env="CACHE_ENABLED")
    cache_max_size: int = Field(default=100, env="CACHE_MAX_SIZE")
    cache_ttl_seconds: int = Field(default=900, env="CACHE_TTL_SECONDS")  # 15 minutes
    cache_similarity_threshold: float = Field(default=0.85, env="CACHE_SIMILARITY_THRESHOLD")

    # User Profile Settings
    profile_enabled: bool = Field(default=True, env="PROFILE_ENABLED")
    profiles_dir: str = Field(default="profiles", env="PROFILES_DIR")
    
    # 3-Tier Memory System
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    
    # Progressive Injection: Variable turn depth based on query complexity
    # Tier 1 queries (90%): 10 turns (~200 tokens)
    # Tier 2 queries (8%): 15 turns (~300 tokens)  
    # Tier 3 queries (2%): 20 turns (~400 tokens)
    working_memory_turns: int = Field(
        default=10, 
        env="WORKING_MEMORY_TURNS",
        description="Default turns for Tier 1 queries (optimized from 20 to 10)"
    )
    working_memory_ttl: int = Field(default=1800, env="WORKING_MEMORY_TTL")
    
    session_memory_model: str = Field(default="gpt-4o-mini", env="SESSION_MEMORY_MODEL")
    session_memory_ttl: int = Field(default=86400, env="SESSION_MEMORY_TTL")
    
    graphiti_enabled: bool = Field(default=True, env="GRAPHITI_ENABLED")
    progressive_injection: bool = Field(
        default=True, 
        env="PROGRESSIVE_INJECTION",
        description="Enable progressive context injection (recommended)"
    )

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")

    # CORS
    cors_origins: str = Field(default="*", env="CORS_ORIGINS")

    class Config:
        env_file = ".env"
        case_sensitive = False


# Model pricing configurations (per 1K tokens)
MODEL_CONFIGS = {
    "gpt-4o": {
        "cost_per_1k_input": 0.0025,
        "cost_per_1k_output": 0.01
    },
    "gpt-4o-mini": {
        "cost_per_1k_input": 0.00015,
        "cost_per_1k_output": 0.0006
    },
    "gpt-4": {
        "cost_per_1k_input": 0.03,
        "cost_per_1k_output": 0.06
    },
    "gpt-3.5-turbo": {
        "cost_per_1k_input": 0.0015,
        "cost_per_1k_output": 0.002
    },
    "claude-3-5-sonnet-20241022": {
        "cost_per_1k_input": 0.003,
        "cost_per_1k_output": 0.015
    },
    "claude-3-5-haiku-20241022": {
        "cost_per_1k_input": 0.001,
        "cost_per_1k_output": 0.005
    }
}

# Global settings instance
settings = Settings()
