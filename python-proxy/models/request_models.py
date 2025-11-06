"""
Modelos Pydantic para requests (OpenAI-compatible)
"""
from typing import List, Optional, Dict, Any, Literal, Union
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Mensagem individual no chat"""
    role: Literal["system", "user", "assistant", "function", "tool"]
    content: Optional[str] = None
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None


class FunctionDefinition(BaseModel):
    """Definição de função para function calling"""
    name: str
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class ChatCompletionRequest(BaseModel):
    """Request compatível com OpenAI Chat Completions"""

    # Campos obrigatórios
    model: str = Field(..., description="ID do modelo ou alias (ex: gpt-4-memory, auto-route)")
    messages: List[ChatMessage] = Field(..., min_items=1)

    # Campos opcionais padrão OpenAI
    temperature: Optional[float] = Field(default=1.0, ge=0, le=2)
    top_p: Optional[float] = Field(default=1.0, ge=0, le=1)
    n: Optional[int] = Field(default=1, ge=1, le=10)
    stream: Optional[bool] = Field(default=False)
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = Field(default=None, ge=1)
    presence_penalty: Optional[float] = Field(default=0, ge=-2, le=2)
    frequency_penalty: Optional[float] = Field(default=0, ge=-2, le=2)
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None

    # Function calling (legacy format)
    functions: Optional[List[FunctionDefinition]] = None
    function_call: Optional[Union[str, Dict[str, str]]] = None

    # Tool calling (newer format - used by MCP)
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None

    # Memory Router custom fields
    memory_enabled: Optional[bool] = Field(
        default=True,
        description="Whether to use memory features (automatic context retrieval)"
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="Conversation ID for tracking multi-turn conversations (auto-generated if not provided)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "user", "content": "What did we discuss yesterday?"}
                ],
                "memory_enabled": True,
                "temperature": 0.7,
                "stream": False
            }
        }


