"""
Memory Router Proxy - Transparent LLM proxy with automatic memory

A simple proxy that sits between Msty Studio and your LLM provider,
automatically managing context and memories like Supermemory's Memory Router.
"""
import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config import settings
from models.request_models import ChatCompletionRequest
from models.response_models import HealthResponse, ErrorResponse
from modules.router import memory_route
from utils.logger import logger
from utils.metrics import metrics_tracker


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


@app.post("/v1/chat/completions")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def chat_completions(
    request: Request,
    body: ChatCompletionRequest,
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_provider_url: Optional[str] = Header(None, alias="X-Provider-URL"),
):
    """
    Main endpoint - OpenAI-compatible with automatic memory.

    Headers:
        Authorization: Bearer {api_key} - LLM provider API key
        X-User-Id: User identifier for memory namespace (optional, uses IP if not provided)
        X-Provider-URL: Override default provider URL (optional)
    """
    request_id = request.state.request_id

    try:
        # Extract API key from Authorization header
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Missing or invalid Authorization header"
            )

        api_key = authorization.replace("Bearer ", "")

        # Determine user_id (for memory namespace)
        user_id = x_user_id or get_remote_address(request)

        # Determine provider URL
        provider_url = x_provider_url or settings.default_provider_url

        # Use default model if not specified
        model = body.model or settings.default_model

        logger.info(
            "processing_request",
            request_id=request_id,
            user_id=user_id,
            model=model,
            messages=len(body.messages),
            memory_enabled=body.memory_enabled
        )

        # Route through memory proxy
        response = memory_route(
            messages=body.messages,
            model=model,
            user_id=user_id,
            provider_url=provider_url,
            api_key=api_key,
            conversation_id=body.conversation_id,
            mcp_search_endpoint=settings.mcp_search_endpoint,
            mcp_store_endpoint=settings.mcp_store_endpoint,
            memory_enabled=body.memory_enabled and settings.memory_enabled,
            memory_max_context_tokens=settings.memory_max_context_tokens,
            memory_chunk_size=settings.memory_chunk_size,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
            stream=body.stream
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

        metrics_tracker.track_request(
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

        # Add custom diagnostic headers (matching Supermemory)
        headers = {
            "X-Memory-Conversation-Id": metadata.get("conversation_id", ""),
            "X-Memory-Context-Modified": str(metadata.get("context_modified", False)),
            "X-Memory-Chunks-Retrieved": str(metadata.get("chunks_retrieved", 0)),
            "X-Memory-Chunks-Created": str(metadata.get("chunks_created", 0)),
            "X-Memory-Tokens-Input": str(metadata.get("tokens_input", 0)),
            "X-Memory-Tokens-Output": str(metadata.get("tokens_output", 0)),
            "X-Memory-Tokens-Memory": str(metadata.get("tokens_memory", 0)),
            "X-Memory-Tokens-Processed": str(metadata.get("tokens_processed", 0)),
            "X-Memory-Processing-Time-Ms": str(int(metadata.get("processing_time_ms", 0)))
        }

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
