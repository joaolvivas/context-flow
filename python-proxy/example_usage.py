"""
Exemplo de uso do Router Module

Demonstra como usar as funções do router.py standalone,
sem necessidade de rodar o servidor FastAPI.
"""
import os
from modules.router import route, classify_intent


def main():
    """Exemplos de uso do router"""

    # Carrega API keys do ambiente
    OPENAI_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")

    if not OPENAI_KEY:
        print("❌ OPENAI_API_KEY não encontrada no ambiente")
        print("Execute: export OPENAI_API_KEY='sk-...'")
        return

    print("=" * 60)
    print("Memory Orchestrator Proxy - Router Example")
    print("=" * 60)

    # ========================================================================
    # EXEMPLO 1: Conversa casual (sem memória)
    # ========================================================================

    print("\\n\\n🤖 EXEMPLO 1: Conversa Casual")
    print("-" * 60)

    prompt = "Olá, tudo bem?"
    print(f"User: {prompt}")

    response = route(
        user_prompt=prompt,
        user_id="user-joao",
        openai_api_key=OPENAI_KEY,
        verbose=True
    )

    print(f"\\nAssistant: {response['choices'][0]['message']['content']}")
    print(f"\\n📊 Metadata:")
    print(f"  - Intent: {response['_router_metadata']['intent']}")
    print(f"  - Model: {response['_router_metadata']['model_selected']}")
    print(f"  - Time: {response['_router_metadata']['processing_time_ms']:.0f}ms")

    # ========================================================================
    # EXEMPLO 2: Recall (busca memória)
    # ========================================================================

    print("\\n\\n🧠 EXEMPLO 2: Recall com Memória")
    print("-" * 60)

    prompt = "Lembra qual link era o meu portfólio?"
    print(f"User: {prompt}")

    response = route(
        user_prompt=prompt,
        user_id="user-joao",
        openai_api_key=OPENAI_KEY,
        mcp_endpoint="http://localhost:5000/mcp/retrieve",  # Ajuste se necessário
        verbose=True
    )

    print(f"\\nAssistant: {response['choices'][0]['message']['content']}")
    print(f"\\n📊 Metadata:")
    print(f"  - Intent: {response['_router_metadata']['intent']}")
    print(f"  - Memories Used: {response['_router_metadata']['memories_used']}")
    print(f"  - Model: {response['_router_metadata']['model_selected']}")

    # ========================================================================
    # EXEMPLO 3: Pergunta complexa (pode usar Claude)
    # ========================================================================

    print("\\n\\n🔍 EXEMPLO 3: Pergunta Complexa")
    print("-" * 60)

    prompt = "Quais são as principais diferenças entre Python e JavaScript para desenvolvimento backend?"
    print(f"User: {prompt}")

    response = route(
        user_prompt=prompt,
        user_id="user-joao",
        openai_api_key=OPENAI_KEY,
        anthropic_api_key=ANTHROPIC_KEY,  # Pode escolher Claude
        verbose=True
    )

    print(f"\\nAssistant: {response['choices'][0]['message']['content'][:200]}...")
    print(f"\\n📊 Metadata:")
    print(f"  - Intent: {response['_router_metadata']['intent']}")
    print(f"  - Model: {response['_router_metadata']['model_selected']}")

    # ========================================================================
    # EXEMPLO 4: Store (armazenar informação)
    # ========================================================================

    print("\\n\\n💾 EXEMPLO 4: Armazenar Informação")
    print("-" * 60)

    prompt = "Guarda essa informação: meu portfolio é https://github.com/joaolucas"
    print(f"User: {prompt}")

    response = route(
        user_prompt=prompt,
        user_id="user-joao",
        openai_api_key=OPENAI_KEY,
        verbose=True
    )

    print(f"\\nAssistant: {response['choices'][0]['message']['content']}")

    # ========================================================================
    # EXEMPLO 5: Teste de classificação
    # ========================================================================

    print("\\n\\n🎯 EXEMPLO 5: Teste de Classificação de Intenções")
    print("-" * 60)

    test_prompts = [
        "Lembra qual link era o meu portfólio?",
        "Oi, tudo bem?",
        "Resume nossa conversa de ontem",
        "Guarda: meu email é joao@example.com",
        "Quais empresas apliquei essa semana?",
        "Explique machine learning",
        "O que é FastAPI?"
    ]

    for test_prompt in test_prompts:
        intent = classify_intent(test_prompt)
        print(f"{intent:12} | {test_prompt}")

    print("\\n" + "=" * 60)
    print("✅ Exemplos concluídos!")
    print("=" * 60)


if __name__ == "__main__":
    main()
