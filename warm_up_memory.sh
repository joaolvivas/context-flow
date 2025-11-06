#!/bin/bash
# ContextFlow Memory Warm-up Script
# 
# Pré-carrega o Redis com fatos básicos do Graphiti
# para que o sistema comece "warm" ao invés de "cold"

set -e

echo "🔥 ContextFlow Memory Warm-up"
echo "=============================="
echo ""

# Verificar se os serviços estão rodando
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Erro: Proxy não está rodando"
    echo "   Execute: bash start_memory_system.sh"
    exit 1
fi

if ! curl -s http://localhost:5001/health > /dev/null 2>&1; then
    echo "❌ Erro: Bridge não está rodando"
    echo "   Execute: bash start_memory_system.sh"
    exit 1
fi

echo "✅ Serviços estão rodando"
echo ""

# Buscar fatos básicos do Graphiti e simular conversas
# Isso popula o working_memory e session_facts no Redis

echo "🔍 Buscando informações básicas do Graphiti..."
echo ""

OPENAI_KEY="${OPENAI_API_KEY}"

if [ -z "$OPENAI_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY não encontrada"
    echo "   Continuando com teste limitado..."
fi

# Queries de warm-up - perguntas comuns que você faz
WARMUP_QUERIES=(
    "Quem sou eu?"
    "Qual é meu background profissional?"
    "Quais são minhas habilidades?"
)

echo "📝 Executando ${#WARMUP_QUERIES[@]} queries de warm-up..."
echo ""

for query in "${WARMUP_QUERIES[@]}"; do
    echo "   → \"$query\""
    
    if [ -n "$OPENAI_KEY" ]; then
        # Fazer request real para popular o Redis
        curl -s -X POST http://localhost:8000/v1/chat/completions \
          -H "Content-Type: application/json" \
          -H "Authorization: Bearer $OPENAI_KEY" \
          -H "X-User-Id: lucas-ai" \
          -d "{
            \"model\": \"gpt-4o-mini\",
            \"messages\": [{\"role\": \"user\", \"content\": \"$query\"}],
            \"max_tokens\": 50
          }" > /dev/null 2>&1
        
        echo "      ✓ Processado e armazenado no Redis"
    else
        echo "      ⚠️  Pulado (sem API key)"
    fi
    
    sleep 1
done

echo ""
echo "=============================="
echo "✅ Warm-up completo!"
echo "=============================="
echo ""

# Mostrar estatísticas do Redis
echo "📊 Redis Status:"
WORKING_MEM=$(redis-cli EXISTS "working_memory:lucas-ai:default-lucas-ai")
if [ "$WORKING_MEM" -eq "1" ]; then
    echo "   ✅ Working memory: Populada"
else
    echo "   ⚠️  Working memory: Vazia (normal se sem API key)"
fi

echo ""
echo "💡 Dica: Execute este script após reiniciar o sistema"
echo "   para começar com memórias pré-carregadas!"
