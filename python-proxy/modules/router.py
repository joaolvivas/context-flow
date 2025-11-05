"""
Router Module - Orquestração Inteligente de Prompts

Baseado no comportamento do SuperMemory Router:
- Classifica intenção do prompt
- Recupera memórias relevantes via MCP/Graphiti
- Enriquece o prompt com contexto
- Escolhe o modelo ideal
- Despacha e retorna resposta
"""
import re
import requests
import json
from typing import Dict, Optional, List, Tuple
from datetime import datetime


# ============================================================================
# CLASSIFICAÇÃO DE INTENÇÃO
# ============================================================================

def classify_intent(prompt: str) -> str:
    """
    Detecta a intenção do usuário baseado em padrões no prompt.

    Args:
        prompt: Texto do usuário

    Returns:
        Uma das seguintes intenções:
        - "recall": Busca por informações passadas
        - "question": Pergunta que precisa de conhecimento externo
        - "summarize": Pedido de resumo ou síntese
        - "store": Instrução para guardar informação
        - "casual": Conversa casual sem necessidade de contexto

    Examples:
        >>> classify_intent("Lembra qual link era o meu portfólio?")
        'recall'
        >>> classify_intent("Olá, como vai?")
        'casual'
    """

    prompt_lower = prompt.lower()

    # Padrões de recall (busca de memória)
    recall_patterns = [
        r"\blembr[ao]",
        r"\bqual (?:era|foi)",
        r"\bvocê (?:sabe|tem)",
        r"\baplicou",
        r"\bfalei sobre",
        r"\bmencionei",
        r"\bhistórico",
        r"\banteriormente"
    ]

    # Padrões de store (armazenar)
    store_patterns = [
        r"\bguard[ae]",
        r"\banot[ae]",
        r"\bsalv[ae]",
        r"\blembr[ae] disso",
        r"\bpreciso que (?:lembre|anote)"
    ]

    # Padrões de summarize
    summarize_patterns = [
        r"\bresume",
        r"\bresumo",
        r"\bsintetize",
        r"\bem poucas palavras",
        r"\bo principal"
    ]

    # Padrões de casual
    casual_patterns = [
        r"^(?:oi|olá|hey|bom dia|boa tarde|boa noite)",
        r"^(?:como vai|tudo bem|e aí)",
        r"^(?:obrigad[oa]|valeu)"
    ]

    # Verifica padrões em ordem de especificidade
    if any(re.search(pattern, prompt_lower) for pattern in store_patterns):
        return "store"

    if any(re.search(pattern, prompt_lower) for pattern in recall_patterns):
        return "recall"

    if any(re.search(pattern, prompt_lower) for pattern in summarize_patterns):
        return "summarize"

    if any(re.search(pattern, prompt_lower) for pattern in casual_patterns):
        return "casual"

    # Se não matched nenhum, assume que é uma pergunta
    return "question"


# ============================================================================
# RECUPERAÇÃO DE MEMÓRIA
# ============================================================================

def retrieve_memory(
    prompt: str,
    user_id: str,
    mcp_endpoint: str = "http://localhost:5000/mcp/retrieve",
    limit: int = 5,
    min_relevance: float = 0.7
) -> str:
    """
    Busca memórias relevantes via MCP/Graphiti.

    Args:
        prompt: Query de busca
        user_id: Identificador do usuário (usado como namespace)
        mcp_endpoint: URL do servidor MCP
        limit: Número máximo de memórias a retornar
        min_relevance: Score mínimo de relevância (0-1)

    Returns:
        String formatada com as memórias encontradas, ou vazia se nenhuma

    Example:
        >>> retrieve_memory("portfolio link", "user-123")
        "Relevant memories:\\n1. Portfolio: https://github.com/user (relevance: 0.95)"
    """

    try:
        # Payload para o MCP
        payload = {
            "query": prompt,
            "user_id": user_id,
            "limit": limit,
            "min_relevance": min_relevance
        }

        # Timeout agressivo para não atrasar resposta
        response = requests.post(
            mcp_endpoint,
            json=payload,
            timeout=1.5  # Máx 1.5s para busca
        )

        if response.status_code != 200:
            print(f"⚠️ MCP returned {response.status_code}: {response.text}")
            return ""

        data = response.json()
        memories = data.get("results", [])

        if not memories:
            return ""

        # Formata memórias de forma concisa
        formatted_memories = []
        for idx, mem in enumerate(memories[:limit], 1):
            name = mem.get("name", "Memory")
            content = mem.get("content", "").strip()
            relevance = mem.get("relevance", 0)

            # Limita tamanho do content
            if len(content) > 200:
                content = content[:197] + "..."

            formatted_memories.append(
                f"{idx}. {name} (relevance: {relevance:.2f})\\n   {content}"
            )

        return "\\n\\n".join(formatted_memories)

    except requests.Timeout:
        print("⚠️ MCP timeout - continuing without memory")
        return ""

    except requests.ConnectionError:
        print("⚠️ MCP not reachable - continuing without memory")
        return ""

    except Exception as e:
        print(f"⚠️ Error retrieving memory: {e}")
        return ""


# ============================================================================
# CONSTRUÇÃO DE PROMPT ENRIQUECIDO
# ============================================================================

def build_prompt(context: str, prompt: str, intent: str) -> str:
    """
    Injeta contexto de memória no prompt de forma estruturada.

    Args:
        context: Memórias recuperadas (pode ser vazio)
        prompt: Prompt original do usuário
        intent: Intenção detectada

    Returns:
        Prompt enriquecido pronto para envio ao modelo

    Example:
        >>> build_prompt("Portfolio: github.com/user", "Qual meu portfólio?", "recall")
        "You have access to the user's memory...\\n\\nUser's question: Qual meu portfólio?"
    """

    if not context:
        # Sem contexto, retorna prompt original
        return prompt

    # Template base
    enriched_prompt = f"""You have access to the user's personal memory and context.

<relevant_context>
{context}
</relevant_context>

Use the context above to provide accurate, personalized responses. If the context doesn't contain relevant information, rely on your general knowledge.

User's question: {prompt}"""

    # Ajustes específicos por intenção
    if intent == "recall":
        enriched_prompt += "\\n\\n(The user is asking about something from their past conversations or stored information. Prioritize the context provided.)"

    elif intent == "summarize":
        enriched_prompt += "\\n\\n(The user wants a concise summary. Be brief and highlight key points.)"

    return enriched_prompt


# ============================================================================
# ESCOLHA DE MODELO
# ============================================================================

def choose_model(intent: str, prompt_length: int = 0) -> str:
    """
    Decide qual modelo usar baseado na intenção e complexidade.

    Args:
        intent: Intenção detectada pelo classify_intent
        prompt_length: Tamanho do prompt (caracteres)

    Returns:
        Nome do modelo a ser usado

    Strategy:
        - casual: modelo rápido e barato (gpt-4o-mini)
        - recall: modelo com boa memória contextual (gpt-4o)
        - question: modelo balanceado (gpt-4-turbo)
        - summarize: modelo bom em síntese (claude-3-5-sonnet)
        - store: não precisa de modelo (retorna ACK direto)
    """

    model_routing = {
        "casual": "gpt-4o-mini",        # Rápido e barato
        "recall": "gpt-4o",              # Excelente com contexto
        "question": "gpt-4-turbo",       # Balanceado
        "summarize": "claude-3-5-sonnet", # Ótimo para síntese
        "store": None  # Não precisa de modelo
    }

    selected_model = model_routing.get(intent, "gpt-4-turbo")

    # Override para prompts muito longos (usa Claude por ter maior context window)
    if prompt_length > 8000:
        selected_model = "claude-3-5-sonnet"

    return selected_model


# ============================================================================
# DISPATCH AO MODELO
# ============================================================================

def dispatch_to_model(
    prompt: str,
    model: str,
    openai_api_key: str,
    anthropic_api_key: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 1000
) -> Dict:
    """
    Envia prompt ao modelo escolhido e retorna resposta.

    Args:
        prompt: Prompt enriquecido
        model: Nome do modelo (gpt-4, claude-3-5-sonnet, etc)
        openai_api_key: API key da OpenAI
        anthropic_api_key: API key da Anthropic (se usar Claude)
        temperature: Controle de criatividade (0-2)
        max_tokens: Máximo de tokens na resposta

    Returns:
        Dicionário no formato OpenAI API:
        {
            "id": "...",
            "model": "...",
            "choices": [{
                "message": {"role": "assistant", "content": "..."},
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": X, "completion_tokens": Y, "total_tokens": Z}
        }
    """

    # Determina provider baseado no modelo
    if model.startswith("claude"):
        return _dispatch_to_anthropic(
            prompt, model, anthropic_api_key, temperature, max_tokens
        )
    else:
        return _dispatch_to_openai(
            prompt, model, openai_api_key, temperature, max_tokens
        )


def _dispatch_to_openai(
    prompt: str,
    model: str,
    api_key: str,
    temperature: float,
    max_tokens: int
) -> Dict:
    """Dispatch específico para OpenAI"""

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30  # 30s max
        )

        if response.status_code != 200:
            raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")

        return response.json()

    except Exception as e:
        # Fallback response em caso de erro
        return {
            "id": "error",
            "model": model,
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": f"Desculpe, ocorreu um erro ao processar sua solicitação: {str(e)}"
                },
                "finish_reason": "error"
            }],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        }


def _dispatch_to_anthropic(
    prompt: str,
    model: str,
    api_key: Optional[str],
    temperature: float,
    max_tokens: int
) -> Dict:
    """Dispatch específico para Anthropic Claude"""

    if not api_key:
        raise Exception("Anthropic API key required for Claude models")

    try:
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]
        }

        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code != 200:
            raise Exception(f"Anthropic API error: {response.status_code} - {response.text}")

        # Converte resposta Anthropic para formato OpenAI
        anthropic_response = response.json()

        return {
            "id": anthropic_response.get("id", "unknown"),
            "model": model,
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": anthropic_response["content"][0]["text"]
                },
                "finish_reason": anthropic_response.get("stop_reason", "stop")
            }],
            "usage": {
                "prompt_tokens": anthropic_response["usage"]["input_tokens"],
                "completion_tokens": anthropic_response["usage"]["output_tokens"],
                "total_tokens": (
                    anthropic_response["usage"]["input_tokens"] +
                    anthropic_response["usage"]["output_tokens"]
                )
            }
        }

    except Exception as e:
        return {
            "id": "error",
            "model": model,
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": f"Desculpe, ocorreu um erro ao processar sua solicitação: {str(e)}"
                },
                "finish_reason": "error"
            }],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        }


# ============================================================================
# FUNÇÃO PRINCIPAL DE ROTEAMENTO
# ============================================================================

def route(
    user_prompt: str,
    user_id: str,
    openai_api_key: str,
    anthropic_api_key: Optional[str] = None,
    mcp_endpoint: str = "http://localhost:5000/mcp/retrieve",
    temperature: float = 0.7,
    max_tokens: int = 1000,
    verbose: bool = False
) -> Dict:
    """
    Função principal: orquestra todo o fluxo de processamento.

    Flow:
        1. Classifica intenção do prompt
        2. Recupera memória (se necessário)
        3. Enriquece o prompt com contexto
        4. Escolhe o modelo ideal
        5. Despacha ao modelo
        6. Retorna resposta

    Args:
        user_prompt: Texto original do usuário
        user_id: ID do usuário (namespace de memória)
        openai_api_key: API key OpenAI
        anthropic_api_key: API key Anthropic (opcional)
        mcp_endpoint: URL do MCP server
        temperature: Criatividade (0-2)
        max_tokens: Máx tokens na resposta
        verbose: Se True, printa logs do processo

    Returns:
        Response no formato OpenAI API

    Example:
        >>> response = route(
        ...     "Lembra qual link era o meu portfólio?",
        ...     "user-joao",
        ...     "sk-..."
        ... )
        >>> print(response["choices"][0]["message"]["content"])
        "Seu portfólio está em https://github.com/user"
    """

    start_time = datetime.now()

    # 1. Classifica intenção
    intent = classify_intent(user_prompt)
    if verbose:
        print(f"🎯 Intent detected: {intent}")

    # 2. Recupera memória (se necessário)
    context = ""
    if intent in ["recall", "question", "summarize"]:
        context = retrieve_memory(user_prompt, user_id, mcp_endpoint)
        if verbose:
            memories_count = len(context.split("\\n\\n")) if context else 0
            print(f"🧠 Memories retrieved: {memories_count}")

    # 3. Enriquece prompt
    enriched_prompt = build_prompt(context, user_prompt, intent)
    prompt_length = len(enriched_prompt)
    if verbose:
        print(f"📝 Prompt enriched ({prompt_length} chars)")

    # 4. Escolhe modelo
    model = choose_model(intent, prompt_length)
    if verbose:
        print(f"🤖 Model selected: {model}")

    # 5. Caso especial: store não precisa de modelo
    if intent == "store":
        # TODO: Implementar armazenamento via MCP
        return {
            "id": "store-ack",
            "model": "none",
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "✅ Informação armazenada com sucesso."
                },
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        }

    # 6. Despacha ao modelo
    response = dispatch_to_model(
        enriched_prompt,
        model,
        openai_api_key,
        anthropic_api_key,
        temperature,
        max_tokens
    )

    # Adiciona metadados do router
    response["_router_metadata"] = {
        "intent": intent,
        "memories_used": len(context.split("\\n\\n")) if context else 0,
        "model_selected": model,
        "processing_time_ms": (datetime.now() - start_time).total_seconds() * 1000
    }

    if verbose:
        print(f"✅ Response ready ({response['_router_metadata']['processing_time_ms']:.0f}ms)")

    return response


# ============================================================================
# TESTES E EXEMPLOS
# ============================================================================

if __name__ == "__main__":
    # Exemplo de uso
    import os

    # Carrega API keys do ambiente
    OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")

    # Testa classificação
    print("\\n=== TESTE DE CLASSIFICAÇÃO ===")
    test_prompts = [
        "Lembra qual link era o meu portfólio?",
        "Olá, tudo bem?",
        "Resume o que discutimos ontem",
        "Guarda essa informação: meu email é joao@example.com",
        "Quais empresas apliquei essa semana?"
    ]

    for prompt in test_prompts:
        intent = classify_intent(prompt)
        print(f"{intent:12} | {prompt}")

    # Testa roteamento completo (se houver API key)
    if OPENAI_KEY:
        print("\\n\\n=== TESTE DE ROTEAMENTO COMPLETO ===")
        response = route(
            "Oi, como vai?",
            "user-test",
            OPENAI_KEY,
            verbose=True
        )
        print(f"\\nResponse: {response['choices'][0]['message']['content']}")
        print(f"Metadata: {response.get('_router_metadata', {})}")
