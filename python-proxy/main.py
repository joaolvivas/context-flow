"""
Memory Orchestrator Proxy - FastAPI Server

Proxy inteligente compatível com OpenAI API que adiciona memória persistente
e roteamento inteligente de modelos para o Msty Studio.
"""
import uuid
import time
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config import settings, PERSONAS
from models.request_models import ChatCompletionRequest, MemorySearchRequest, MemoryAddRequest
from models.response_models import (
    ChatCompletionResponse,
    HealthResponse,
    MetricsResponse,
    MemorySearchResponse,
    MemoryAddResponse,
    ErrorResponse
)
from utils.logger import logger, request_logger
from utils.metrics import metrics_tracker


# Lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia startup e shutdown da aplicação"""
    # Startup
    logger.info("🚀 Starting Memory Orchestrator Proxy", port=settings.port)

    # Verifica conexões (Neo4j, Graphiti, etc)
    # TODO: Adicionar health checks aqui

    yield

    # Shutdown
    logger.info("Shutting down Memory Orchestrator Proxy")


# Inicializa FastAPI
app = FastAPI(
    title="Memory Orchestrator Proxy",
    description="Proxy inteligente com memória persistente para Msty Studio",
    version="1.0.0",
    lifespan=lifespan
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
origins = settings.cors_origins.split(",") if settings.cors_origins != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware para logging de requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware para logging automático de todas as requests"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    request.state.start_time = time.time()

    logger.info(
        "request_started",
        request_id=request_id,
        method=request.method,
        path=request.url.path
    )

    response = await call_next(request)

    duration_ms = (time.time() - request.state.start_time) * 1000

    logger.info(
        "request_completed",
        request_id=request_id,
        status_code=response.status_code,
        duration_ms=round(duration_ms, 2)
    )

    return response


# ============================================================================
# ENDPOINTS PRINCIPAIS
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check do serviço

    Verifica status de todas as dependências
    """
    # TODO: Implementar checks reais de Neo4j, Graphiti, etc
    components = {
        "graphiti": settings.graphiti_mcp_enabled,
        "neo4j": True,  # TODO: Verificar conexão real
        "openai": bool(settings.openai_api_key),
        "anthropic": bool(settings.anthropic_api_key)
    }

    all_healthy = all(components.values())

    return HealthResponse(
        status="ok" if all_healthy else "degraded",
        timestamp=datetime.now(),
        components=components,
        memory={
            "enabled": settings.graphiti_mcp_enabled,
            "auto_store": settings.memory_auto_store
        }
    )


@app.get("/metrics", response_model=MetricsResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def get_metrics(request: Request):
    """
    Retorna métricas do proxy

    Inclui: requests, custos, tokens, tempos de resposta, uso de memória
    """
    stats = metrics_tracker.get_stats()
    return MetricsResponse(**stats)


@app.post("/v1/chat/completions")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def chat_completions(
    request: Request,
    body: ChatCompletionRequest,
    x_persona: Optional[str] = Header(None, alias="X-Persona")
):
    """
    Endpoint principal compatível com OpenAI Chat Completions

    Suporta:
    - Memória contextual via Graphiti
    - Roteamento inteligente de modelos
    - Múltiplas personas com namespaces
    - Streaming de responses
    - Function calling
    """
    request_id = request.state.request_id
    start_time = time.time()

    try:
        # 1. Determina persona
        persona = x_persona or body.persona or settings.default_persona

        if persona not in PERSONAS:
            raise HTTPException(
                status_code=400,
                detail=f"Persona '{persona}' não encontrada. Disponíveis: {list(PERSONAS.keys())}"
            )

        request_logger.log_request(
            request_id=request_id,
            persona=persona,
            model=body.model,
            message_count=len(body.messages),
            stream=body.stream
        )

        # 2. Análise de intenção
        # TODO: Implementar módulo de análise

        # 3. Recuperação de memória
        # TODO: Implementar busca via Graphiti

        # 4. Roteamento de modelo
        # TODO: Implementar seleção inteligente

        # 5. Enriquecimento de prompt
        # TODO: Injetar contexto de memória

        # 6. Chamada ao provider (OpenAI, Anthropic, etc)
        # TODO: Implementar providers

        # Placeholder response por enquanto
        response_time_ms = (time.time() - start_time) * 1000

        # Mock response
        mock_response = {
            "id": f"chatcmpl-{request_id[:8]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": body.model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": f"[MOCK] Você está usando a persona '{persona}'. Implementação completa em breve!"
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        }

        # Log metrics
        metrics_tracker.track_request(
            model=body.model,
            persona=persona,
            tokens_input=10,
            tokens_output=20,
            response_time_ms=response_time_ms,
            memories_used=0
        )

        request_logger.log_response(
            request_id=request_id,
            model=body.model,
            total_time_ms=response_time_ms,
            tokens_input=10,
            tokens_output=20,
            cost_usd=0.0001,
            memories_used=0
        )

        return JSONResponse(content=mock_response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "chat_completion_error",
            request_id=request_id,
            error=str(e),
            exc_info=True
        )

        metrics_tracker.track_request(
            model=body.model,
            persona=persona,
            tokens_input=0,
            tokens_output=0,
            response_time_ms=0,
            error=True
        )

        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "message": str(e),
                    "type": "internal_error",
                    "code": "proxy_error"
                }
            }
        )


# ============================================================================
# ENDPOINTS DE MEMÓRIA
# ============================================================================

@app.post("/memory/search", response_model=MemorySearchResponse)
async def search_memory(request: Request, body: MemorySearchRequest):
    """
    Busca memórias diretamente via API

    Útil para debugging ou acesso direto ao grafo de conhecimento
    """
    request_id = request.state.request_id
    start_time = time.time()

    try:
        # TODO: Implementar busca real via Graphiti
        search_time_ms = (time.time() - start_time) * 1000

        return MemorySearchResponse(
            query=body.query,
            results=[],
            total_found=0,
            search_time_ms=search_time_ms
        )

    except Exception as e:
        logger.error("memory_search_error", request_id=request_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/add", response_model=MemoryAddResponse)
async def add_memory(request: Request, body: MemoryAddRequest):
    """
    Adiciona memória manualmente ao grafo

    Útil para popular o grafo ou corrigir informações
    """
    request_id = request.state.request_id

    try:
        # TODO: Implementar adição via Graphiti
        return MemoryAddResponse(
            success=True,
            message="Memória adicionada com sucesso (mock)",
            memory_id=str(uuid.uuid4())
        )

    except Exception as e:
        logger.error("memory_add_error", request_id=request_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/stats")
async def memory_stats(request: Request):
    """
    Estatísticas do grafo de conhecimento

    Retorna contadores de entidades, facts, etc
    """
    try:
        # TODO: Buscar stats reais do Neo4j/Graphiti
        return {
            "total_entities": 0,
            "total_facts": 0,
            "by_namespace": {},
            "by_persona": {}
        }

    except Exception as e:
        logger.error("memory_stats_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS DE PERSONAS
# ============================================================================

@app.get("/personas")
async def list_personas():
    """Lista todas as personas disponíveis"""
    return {
        "personas": PERSONAS,
        "default": settings.default_persona
    }


@app.get("/personas/{persona_name}")
async def get_persona(persona_name: str):
    """Detalhes de uma persona específica"""
    if persona_name not in PERSONAS:
        raise HTTPException(
            status_code=404,
            detail=f"Persona '{persona_name}' não encontrada"
        )

    return {
        "name": persona_name,
        **PERSONAS[persona_name]
    }


# ============================================================================
# STARTUP
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    logger.info(
        "🚀 Starting server",
        host=settings.host,
        port=settings.port,
        debug=settings.debug
    )

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
