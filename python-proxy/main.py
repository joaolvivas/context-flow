"""
Memory Router Proxy - Transparent LLM proxy with automatic memory

A simple proxy that sits between Msty Studio and your LLM provider,
automatically managing context and memories like Supermemory's Memory Router.
"""
import re
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config import settings
from models.request_models import ChatCompletionRequest
from models.response_models import HealthResponse, ErrorResponse
from modules.router_v3 import memory_route_v3, get_memory_system
from modules.backends import get_backend
from utils.logger import logger
from utils.metrics import metrics_tracker

# LangGraph V4 (optional, conditional import)
try:
    from modules.router_langgraph_v4 import memory_route_langgraph
    LANGGRAPH_AVAILABLE = True
    logger.info("✓ LangGraph V4 agent orchestration available")
except ImportError as e:
    LANGGRAPH_AVAILABLE = False
    logger.warning(f"⚠ LangGraph V4 not available: {e}")
from pydantic import BaseModel
class SeedMemoryRequest(BaseModel):
    """Payload to preload Tier 1 and Tier 2 with core identity info."""

    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    clear_existing: bool = True



def sanitize_header_value(value: Optional[str], max_length: int = 200) -> Optional[str]:
    """Ensure header value is ASCII-only and free of newlines."""
    if value is None:
        return None

    sanitized = str(value).replace("\n", " ").replace("\r", " ")
    sanitized = sanitized.encode("ascii", "ignore").decode("ascii")
    sanitized = sanitized.strip()

    if not sanitized:
        return None

    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized


# Initialize FastAPI
app = FastAPI(
    title="Memory Router Proxy",
    description="Transparent LLM proxy with automatic memory management",
    version="1.0.0"
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


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    logger.info(
        "request",
        request_id=request_id,
        method=request.method,
        path=request.url.path
    )

    response = await call_next(request)
    return response


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(),
        components={
            "memory": settings.memory_enabled
        },
        memory={
            "enabled": settings.memory_enabled
        }
    )


@app.get("/metrics")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def get_metrics(request: Request):
    """Get proxy metrics"""
    stats = metrics_tracker.get_stats()
    return stats


@app.post("/v1/memory/seed")
async def seed_memory(payload: SeedMemoryRequest):
    """Seed Tier 1 and Tier 2 with base profile data fetched from Graphiti."""

    if settings.memory_backend != "graphiti":
        raise HTTPException(status_code=400, detail="Memory seeding requires Graphiti backend")

    user_id = payload.user_id or settings.default_user_id
    conversation_id = payload.conversation_id or f"default-{user_id}"

    memory_router = get_memory_system()

    if payload.clear_existing:
        try:
            memory_router.working_memory.clear_conversation(user_id, conversation_id)
        except Exception as exc:
            logger.warning("seed_memory_clear_failed", error=str(exc))

    backend = get_backend(
        "graphiti",
        search_endpoint=settings.mcp_search_endpoint,
        store_endpoint=settings.mcp_store_endpoint,
        chunk_size=settings.memory_chunk_size,
        model=settings.default_model,
    )

    profile_queries = [
        "Resumo completo do perfil profissional do João Lucas Vivas",
        "Quais são os objetivos profissionais de João Lucas Vivas",
        "Quais plataformas e ferramentas João Lucas Vivas utiliza",
        "Informações principais sobre João Lucas Vivas"
    ]

    snippets: List[str] = []
    seen: set[str] = set()

    for query in profile_queries:
        try:
            results = backend.search(query, user_id, limit=3) or []
        except Exception as exc:
            logger.error("seed_memory_graphiti_error", query=query, error=str(exc))
            continue

        for item in results:
            content = (item.get("content") or "").strip()
            if content and content not in seen:
                snippets.append(content)
                seen.add(content)

    extra_snippets = [
        "João Lucas Vivas tem um cachorro chamado Koda (American Bully).",
        "João Lucas Vivas é torcedor do Botafogo e acompanha o clube com paixão.",
        "A cor favorita de João Lucas Vivas é preta."
    ]

    for extra in extra_snippets:
        if extra not in seen:
            snippets.append(extra)
            seen.add(extra)

    if not snippets:
        raise HTTPException(status_code=404, detail="Não foi possível recuperar dados do Graphiti")

    base_profile_text = "\n".join(snippets)
    seed_message = (
        "Contexto base sobre João Lucas Vivas:\n"
        f"{base_profile_text}\n\n"
        "Use estas informações como memória imediata antes de consultar camadas mais profundas."
    )

    memory_router.working_memory.add_turn(user_id, conversation_id, "system", seed_message)

    facts: List[Dict[str, str]] = []
    for snippet in snippets:
        category = "profile"
        lowered = snippet.lower()
        if any(word in lowered for word in ["objetivo", "goal", "meta"]):
            category = "goal"
        elif any(word in lowered for word in ["plataforma", "platform", "ferramenta", "tool"]):
            category = "tools"
        elif any(word in lowered for word in ["link", "linkedin", "portfólio", "portfolio"]):
            category = "links"
        elif any(word in lowered for word in ["cachorro", "dog", "koda", "pet"]):
            category = "pets"
        elif any(word in lowered for word in ["botafogo", "time", "clube", "time de futebol"]):
            category = "team"
        elif any(word in lowered for word in ["cor favorita", "favorite color", "preta", "preto"]):
            category = "preference"
        elif any(word in lowered for word in ["profissional", "carreira", "marketing", "media buyer"]):
            category = "biography"
        facts.append({"category": category, "fact": snippet})

    stored_count = memory_router.session_memory.store_facts(user_id, conversation_id, facts)

    logger.info(
        "seed_memory_completed",
        user_id=user_id,
        conversation_id=conversation_id,
        facts=stored_count,
    )

    return {
        "success": True,
        "user_id": user_id,
        "conversation_id": conversation_id,
        "facts_added": stored_count,
        "snippets": snippets,
    }


@app.get("/v1/memory/peek")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def memory_peek(request: Request, user_id: Optional[str] = None, conversation_id: Optional[str] = None, q: Optional[str] = None, turns: int = 10, facts: int = 5):
    """Quick inspection of Tier1/2 memory for a user.

    Params:
    - user_id: defaults to settings.default_user_id
    - conversation_id: defaults to `default-{user_id}`
    - q: optional query to filter facts
    - turns: number of recent turns to show
    - facts: number of facts to show
    """
    _user = user_id or settings.default_user_id
    _conv = conversation_id or f"default-{_user}"

    router = get_memory_system()

    # Tier 1
    recent = router.working_memory.get_recent_turns(_user, _conv, limit=turns)
    recent_formatted = router.working_memory.format_as_context(_user, _conv, limit=turns)

    # Tier 2
    facts_matches = router.session_memory.search_facts(_user, _conv, q or "", limit=facts) if q else router.session_memory.get_facts(_user, _conv)[:facts]
    facts_formatted = router.session_memory.format_as_context(_user, _conv, query=q, limit=facts)

    return {
        "user_id": _user,
        "conversation_id": _conv,
        "tier1": {"turns": recent[-turns:], "formatted": recent_formatted},
        "tier2": {"facts": facts_matches, "formatted": facts_formatted},
    }


async def handle_chat_completion(
    request: Request,
    body: ChatCompletionRequest,
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_provider_url: Optional[str] = Header(None, alias="X-Provider-URL"),
):
    """
    Shared handler for chat completion requests.

    Headers:
        Authorization: Bearer {api_key} - LLM provider API key
        X-User-Id: User identifier for memory namespace (optional, uses IP if not provided)
        X-Provider-URL: Override default provider URL (optional)
    """
    request_id = request.state.request_id

    try:
        # Extract API key from Authorization header
        # Allow local model routing with missing/placeholder auth
        if not authorization or not authorization.startswith("Bearer "):
            # Use placeholder for local model routing
            api_key = "local-dev"
        else:
            api_key = authorization.replace("Bearer ", "")

        # Determine user_id (for memory namespace)
        # Use header if provided, otherwise use fixed default user_id for shared memory
        # This ensures all clients share the same memory context
        user_id = x_user_id or settings.default_user_id

        # Determine provider URL
        provider_url = x_provider_url or settings.default_provider_url

        # Use default model if not specified
        model = body.model or settings.default_model

        # Determine user messages for intent checks
        user_messages_raw = [msg for msg in body.messages if msg.role == "user" and (msg.content or "")] 

        # Determine if Tier 3 should be forced
        force_tier3 = bool(body.force_tier3)
        if not force_tier3:
            header_force = request.headers.get("X-Force-Tier3")
            if header_force and header_force.lower() in {"true", "1", "yes", "on"}:
                force_tier3 = True
        if not force_tier3 and user_messages_raw:
            last_content = user_messages_raw[-1].content or ""
            if re.search(r"(usar|use|consultar|procure).*(tier\s*3|graphiti)", last_content, re.IGNORECASE):
                force_tier3 = True

        logger.info(
            "processing_request",
            request_id=request_id,
            user_id=user_id,
            model=model,
            messages=len(body.messages),
            memory_enabled=body.memory_enabled
        )

        # Prepare backend configuration
        backend_config = {}
        if settings.memory_backend == "graphiti":
            backend_config = {
                "search_endpoint": settings.mcp_search_endpoint,
                "store_endpoint": settings.mcp_store_endpoint,
                "chunk_size": settings.memory_chunk_size,
                "model": model
            }
        elif settings.memory_backend == "supermemory":
            backend_config = {
                "base_url": settings.supermemory_base_url,
                "api_key": settings.supermemory_api_key,
                "model": model
            }

        # Convert Pydantic models to dicts for memory_route
        messages_dicts = [msg.dict() if hasattr(msg, 'dict') else msg for msg in body.messages]

        # Prepare extra parameters to pass through to LLM (for MCP tool calls)
        extra_params = {}
        if body.presence_penalty is not None:
            extra_params['presence_penalty'] = body.presence_penalty
        if body.frequency_penalty is not None:
            extra_params['frequency_penalty'] = body.frequency_penalty
        if body.top_p is not None:
            extra_params['top_p'] = body.top_p
        if body.n is not None:
            extra_params['n'] = body.n
        if body.stop is not None:
            extra_params['stop'] = body.stop
        if body.logit_bias is not None:
            extra_params['logit_bias'] = body.logit_bias
        if body.user is not None:
            extra_params['user'] = body.user

        # Route through memory system (V4 LangGraph or V3 fallback)
        use_langgraph = (
            LANGGRAPH_AVAILABLE and
            settings.langgraph_enabled and
            not body.stream  # LangGraph doesn't support streaming yet
        )

        if use_langgraph:
            logger.info("🤖 Using LangGraph V4 agent orchestration")
            response = memory_route_langgraph(
                messages=messages_dicts,
                model=model,
                user_id=user_id,
                provider_url=provider_url,
                api_key=api_key,
                conversation_id=body.conversation_id,
                backend_type=settings.memory_backend,
                backend_config=backend_config,
                memory_enabled=body.memory_enabled and settings.memory_enabled,
                temperature=body.temperature,
                max_tokens=body.max_tokens,
                stream=body.stream,
                tools=body.tools,
                tool_choice=body.tool_choice,
                functions=body.functions,
                function_call=body.function_call,
                force_graphiti=force_tier3,
                **extra_params
            )
        else:
            if body.stream:
                logger.info("📡 Using V3 (streaming not supported in V4)")
            else:
                logger.info("🔄 Using V3 memory routing")

            response = memory_route_v3(
                messages=messages_dicts,
                model=model,
                user_id=user_id,
                provider_url=provider_url,
                api_key=api_key,
                conversation_id=body.conversation_id,
                backend_type=settings.memory_backend,
                backend_config=backend_config,
                memory_enabled=body.memory_enabled and settings.memory_enabled,
                temperature=body.temperature,
                max_tokens=body.max_tokens,
                stream=body.stream,
                tools=body.tools,
                tool_choice=body.tool_choice,
                functions=body.functions,
                function_call=body.function_call,
                force_graphiti=force_tier3,
                **extra_params
            )

        # Handle streaming
        if body.stream:
            # TODO: Implement streaming with memory headers
            return StreamingResponse(
                response.iter_content(chunk_size=8192),
                media_type="text/event-stream"
            )

        # Track metrics
        usage = response.get("usage", {})
        metadata = response.get("_memory_metadata", {})

        track_result = metrics_tracker.track_request(
            model=model,
            persona=user_id[:8],  # Short user_id for metrics
            tokens_input=usage.get("prompt_tokens", 0),
            tokens_output=usage.get("completion_tokens", 0),
            response_time_ms=metadata.get("processing_time_ms", 0),
            memories_used=metadata.get("chunks_retrieved", 0)
        )

        logger.info(
            "request_completed",
            request_id=request_id,
            model=model,
            memories_retrieved=metadata.get("chunks_retrieved", 0),
            context_modified=metadata.get("context_modified", False),
            tokens=usage.get("total_tokens", 0)
        )

        # Add enhanced diagnostic headers with tier information
        headers = {
            # Core memory headers
            "X-Memory-Conversation-Id": metadata.get("conversation_id", ""),
            "X-Memory-Tiers-Used": ",".join(metadata.get("tiers_used", [])),
            
            # Tier-specific metrics
            "X-Memory-Tier1-Turns": str(metadata.get("tier_1_turns", 0)),
            "X-Memory-Tier2-Facts": str(metadata.get("tier_2_facts", 0)),
            "X-Memory-Tier3-Memories": str(metadata.get("tier_3_memories", 0)),

            # Token metrics
            "X-Memory-Tokens-Input": str(metadata.get("tokens_input", 0)),
            "X-Memory-Tokens-Output": str(metadata.get("tokens_output", 0)),
            "X-Memory-Tokens-Memory": str(metadata.get("tokens_memory", 0)),
            "X-Memory-Cost-Estimate": str(metadata.get("total_cost_estimate", 0)),

            # Performance
            "X-Memory-Processing-Time-Ms": str(int(metadata.get("processing_time_ms", 0))),
            "X-Memory-Enabled": str(metadata.get("memory_enabled", False))
        }

        if track_result and not track_result.get("error"):
            headers["X-Memory-Cost-Usd"] = str(round(track_result.get("cost_usd", 0), 6))
            total_tokens = metadata.get("tokens_input", 0) + metadata.get("tokens_output", 0)
            headers["X-Memory-Tokens-Total"] = str(total_tokens)

        # Optional diagnostics
        if metadata.get("why_tier3"):
            sanitized = sanitize_header_value(metadata.get("why_tier3"), max_length=100)
            if sanitized:
                headers["X-Memory-Why-Tier3"] = sanitized
        if metadata.get("cache_reason"):
            sanitized = sanitize_header_value(metadata.get("cache_reason"), max_length=100)
            if sanitized:
                headers["X-Memory-Cache-Reason"] = sanitized
        if metadata.get("context_preview"):
            sanitized_preview = sanitize_header_value(metadata.get("context_preview"), max_length=200)
            if sanitized_preview:
                headers["X-Memory-Context-Preview"] = sanitized_preview
        headers["X-Memory-Force-Tier3"] = str(force_tier3)

        # Add error header if there was an error
        if metadata.get("error"):
            headers["X-Memory-Error"] = str(metadata.get("error"))

        # Remove internal metadata before returning
        if "_memory_metadata" in response:
            del response["_memory_metadata"]

        return JSONResponse(content=response, headers=headers)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "request_error",
            request_id=request_id,
            error=str(e),
            exc_info=True
        )

        # Track error
        metrics_tracker.track_request(
            model=body.model or "unknown",
            persona="error",
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
                    "type": "proxy_error",
                    "code": "internal_error"
                }
            }
        )


# OpenAI-compatible endpoint
@app.post("/v1/chat/completions")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def chat_completions_v1(
    request: Request,
    body: ChatCompletionRequest,
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_provider_url: Optional[str] = Header(None, alias="X-Provider-URL"),
):
    """OpenAI-compatible endpoint: /v1/chat/completions"""
    return await handle_chat_completion(request, body, authorization, x_user_id, x_provider_url)


# Msty-compatible endpoint (without /v1 prefix)
@app.post("/chat/completions")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def chat_completions_msty(
    request: Request,
    body: ChatCompletionRequest,
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_provider_url: Optional[str] = Header(None, alias="X-Provider-URL"),
):
    """Msty-compatible endpoint: /chat/completions"""
    return await handle_chat_completion(request, body, authorization, x_user_id, x_provider_url)


@app.get("/")
async def root():
    """Root endpoint with usage info"""
    return {
        "service": "Memory Router Proxy",
        "version": "1.0.0",
        "description": "Transparent LLM proxy with automatic memory management",
        "endpoints": {
            "health": "GET /health",
            "metrics": "GET /metrics",
            "chat": "POST /v1/chat/completions"
        },
        "usage": {
            "base_url": f"http://localhost:{settings.port}/v1",
            "headers": {
                "Authorization": "Bearer your-llm-provider-api-key",
                "X-User-Id": "user-identifier (optional)",
                "X-Provider-URL": "https://api.openai.com/v1 (optional)"
            }
        }
    }


if __name__ == "__main__":
    import uvicorn

    logger.info(
        "starting_server",
        host=settings.host,
        port=settings.port,
        memory_enabled=settings.memory_enabled
    )

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
