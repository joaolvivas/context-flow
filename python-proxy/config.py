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

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")

    # CORS
    cors_origins: str = Field(default="*", env="CORS_ORIGINS")

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
