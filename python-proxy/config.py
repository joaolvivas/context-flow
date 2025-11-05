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

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")

    # CORS
    cors_origins: str = Field(default="*", env="CORS_ORIGINS")

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
