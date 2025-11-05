"""
Configuração centralizada do Memory Orchestrator Proxy
"""
import os
from typing import Dict, List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Configurações da aplicação carregadas do .env"""

    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="info", env="LOG_LEVEL")

    # API Keys
    openai_api_key: str = Field(env="OPENAI_API_KEY")
    openai_org_id: Optional[str] = Field(default=None, env="OPENAI_ORG_ID")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    google_api_key: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    groq_api_key: Optional[str] = Field(default=None, env="GROQ_API_KEY")

    # Neo4j
    neo4j_uri: str = Field(default="bolt://localhost:7687", env="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", env="NEO4J_USER")
    neo4j_password: str = Field(env="NEO4J_PASSWORD")
    neo4j_database: str = Field(default="neo4j", env="NEO4J_DATABASE")

    # Graphiti MCP
    graphiti_mcp_command: str = Field(
        default="npx @getzep/mcp-server-graphiti",
        env="GRAPHITI_MCP_COMMAND"
    )
    graphiti_mcp_enabled: bool = Field(default=True, env="GRAPHITI_MCP_ENABLED")

    # Memory
    memory_search_limit: int = Field(default=10, env="MEMORY_SEARCH_LIMIT")
    memory_min_relevance: float = Field(default=0.7, env="MEMORY_MIN_RELEVANCE")
    memory_auto_store: bool = Field(default=True, env="MEMORY_AUTO_STORE")

    # Model Routing
    default_model: str = Field(default="gpt-4-turbo", env="DEFAULT_MODEL")
    fast_model: str = Field(default="gpt-4o-mini", env="FAST_MODEL")
    reasoning_model: str = Field(default="claude-3-5-sonnet", env="REASONING_MODEL")
    coding_model: str = Field(default="gpt-4", env="CODING_MODEL")

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_per_hour: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR")

    # Cache
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    cache_enabled: bool = Field(default=True, env="CACHE_ENABLED")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")

    # Persona
    default_persona: str = Field(default="default", env="DEFAULT_PERSONA")
    persona_isolation: bool = Field(default=True, env="PERSONA_ISOLATION")

    # Cost Tracking
    track_costs: bool = Field(default=True, env="TRACK_COSTS")
    cost_alert_threshold: float = Field(default=50.0, env="COST_ALERT_THRESHOLD")

    # CORS
    cors_origins: str = Field(default="*", env="CORS_ORIGINS")

    class Config:
        env_file = ".env"
        case_sensitive = False


# Configuração de Personas
PERSONAS: Dict[str, Dict] = {
    "default": {
        "namespaces": ["general"],
        "default_model": "gpt-4-turbo",
        "memory_enabled": True,
        "description": "Persona padrão para uso geral"
    },
    "job-seeker": {
        "namespaces": ["applications", "companies", "skills", "interviews"],
        "default_model": "gpt-4",
        "memory_enabled": True,
        "description": "Persona para busca de emprego e aplicações"
    },
    "developer": {
        "namespaces": ["code", "learning", "projects", "bugs"],
        "default_model": "claude-3-5-sonnet",
        "memory_enabled": True,
        "description": "Persona para desenvolvimento e aprendizado técnico"
    },
    "marketer": {
        "namespaces": ["campaigns", "metrics", "clients", "insights"],
        "default_model": "gpt-4",
        "memory_enabled": True,
        "description": "Persona para marketing e análise de campanhas"
    },
    "researcher": {
        "namespaces": ["papers", "notes", "experiments", "findings"],
        "default_model": "claude-3-5-sonnet",
        "memory_enabled": True,
        "description": "Persona para pesquisa e análise acadêmica"
    }
}

# Configuração de Modelos
MODEL_CONFIGS = {
    "gpt-4": {
        "provider": "openai",
        "context_window": 128000,
        "cost_per_1k_input": 0.03,
        "cost_per_1k_output": 0.06,
        "supports_streaming": True,
        "supports_functions": True
    },
    "gpt-4-turbo": {
        "provider": "openai",
        "context_window": 128000,
        "cost_per_1k_input": 0.01,
        "cost_per_1k_output": 0.03,
        "supports_streaming": True,
        "supports_functions": True
    },
    "gpt-4o": {
        "provider": "openai",
        "context_window": 128000,
        "cost_per_1k_input": 0.005,
        "cost_per_1k_output": 0.015,
        "supports_streaming": True,
        "supports_functions": True
    },
    "gpt-4o-mini": {
        "provider": "openai",
        "context_window": 128000,
        "cost_per_1k_input": 0.00015,
        "cost_per_1k_output": 0.0006,
        "supports_streaming": True,
        "supports_functions": True
    },
    "claude-3-5-sonnet": {
        "provider": "anthropic",
        "context_window": 200000,
        "cost_per_1k_input": 0.003,
        "cost_per_1k_output": 0.015,
        "supports_streaming": True,
        "supports_functions": True
    },
    "claude-3-haiku": {
        "provider": "anthropic",
        "context_window": 200000,
        "cost_per_1k_input": 0.00025,
        "cost_per_1k_output": 0.00125,
        "supports_streaming": True,
        "supports_functions": True
    }
}

# Mapeamento de modelos "memory" para modelos reais
MODEL_ALIASES = {
    "gpt-4-memory": "gpt-4",
    "gpt-4o-memory": "gpt-4o",
    "gpt-4o-mini-memory": "gpt-4o-mini",
    "claude-3-5-sonnet-memory": "claude-3-5-sonnet",
    "claude-3-haiku-memory": "claude-3-haiku",
    "auto-route": "auto"  # Roteamento automático
}

# Categorias de tarefas para roteamento inteligente
TASK_CATEGORIES = {
    "quick_answer": {
        "model": "gpt-4o-mini",
        "keywords": ["what is", "who is", "define", "explain briefly"]
    },
    "deep_analysis": {
        "model": "claude-3-5-sonnet",
        "keywords": ["analyze", "compare", "evaluate", "deep dive", "comprehensive"]
    },
    "code_generation": {
        "model": "gpt-4",
        "keywords": ["write code", "implement", "create function", "debug", "refactor"]
    },
    "creative_writing": {
        "model": "claude-3-5-sonnet",
        "keywords": ["write", "compose", "draft", "create content"]
    },
    "data_analysis": {
        "model": "gpt-4",
        "keywords": ["analyze data", "calculate", "statistics", "metrics"]
    }
}


# Instância global de configurações
settings = Settings()
