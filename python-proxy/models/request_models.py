"""
Modelos Pydantic para requests (OpenAI-compatible)
"""
from typing import List, Optional, Dict, Any, Literal, Union
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Mensagem individual no chat"""
    role: Literal["system", "user", "assistant", "function"]
    content: Optional[str] = None
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None


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

    # Function calling
    functions: Optional[List[FunctionDefinition]] = None
    function_call: Optional[Union[str, Dict[str, str]]] = None

    # Campos customizados do proxy
    persona: Optional[str] = Field(
        default=None,
        description="Persona a ser utilizada (job-seeker, developer, etc)"
    )
    memory_enabled: Optional[bool] = Field(
        default=True,
        description="Se deve usar memória contextual"
    )
    memory_namespaces: Optional[List[str]] = Field(
        default=None,
        description="Namespaces específicos para buscar memórias"
    )
    auto_store_memory: Optional[bool] = Field(
        default=True,
        description="Se deve armazenar esta conversa automaticamente"
    )
    task_hint: Optional[str] = Field(
        default=None,
        description="Dica de tipo de tarefa para roteamento (quick_answer, deep_analysis, etc)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "model": "gpt-4-memory",
                "messages": [
                    {"role": "user", "content": "Quais empresas eu já apliquei?"}
                ],
                "persona": "job-seeker",
                "temperature": 0.7,
                "stream": False
            }
        }


class MemorySearchRequest(BaseModel):
    """Request para busca de memórias via API"""
    query: str = Field(..., min_length=1, max_length=1000)
    persona: Optional[str] = None
    namespaces: Optional[List[str]] = None
    limit: Optional[int] = Field(default=10, ge=1, le=50)
    min_relevance: Optional[float] = Field(default=0.7, ge=0, le=1)


class MemoryAddRequest(BaseModel):
    """Request para adicionar memória via API"""
    content: str = Field(..., min_length=1)
    name: Optional[str] = None
    persona: Optional[str] = None
    namespaces: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
