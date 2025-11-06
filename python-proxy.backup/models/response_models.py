"""
Modelos Pydantic para responses (OpenAI-compatible)
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class ChatCompletionChoice(BaseModel):
    """Choice individual em response"""
    index: int
    message: Dict[str, Any]
    finish_reason: Optional[Literal["stop", "length", "function_call", "content_filter"]] = None


class ChatCompletionUsage(BaseModel):
    """Uso de tokens"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    """Response compatível com OpenAI"""
    id: str = Field(..., description="ID único da completion")
    object: Literal["chat.completion"] = "chat.completion"
    created: int = Field(..., description="Timestamp Unix")
    model: str = Field(..., description="Modelo utilizado")
    choices: List[ChatCompletionChoice]
    usage: ChatCompletionUsage

    # Campos customizados do proxy (opcionais, compatíveis com OpenAI)
    system_fingerprint: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "chatcmpl-123",
                "object": "chat.completion",
                "created": 1677652288,
                "model": "gpt-4",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Você aplicou para as seguintes empresas: Vercel, Linear, Notion."
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": 56,
                    "completion_tokens": 31,
                    "total_tokens": 87
                }
            }
        }


class StreamChoice(BaseModel):
    """Choice em streaming"""
    index: int
    delta: Dict[str, Any]
    finish_reason: Optional[str] = None


class ChatCompletionChunk(BaseModel):
    """Chunk individual em streaming"""
    id: str
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int
    model: str
    choices: List[StreamChoice]


class HealthResponse(BaseModel):
    """Response do health check"""
    status: Literal["ok", "degraded", "error"]
    service: str = "memory-router-proxy"
    version: str = "1.0.0"
    timestamp: datetime
    components: Dict[str, bool]
    memory: Dict[str, Any]


class ErrorResponse(BaseModel):
    """Response padrão de erro (compatível com OpenAI)"""
    error: Dict[str, Any] = Field(
        ...,
        description="Objeto de erro com message, type, code, etc"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "error": {
                    "message": "Invalid API key provided",
                    "type": "invalid_request_error",
                    "code": "invalid_api_key"
                }
            }
        }
