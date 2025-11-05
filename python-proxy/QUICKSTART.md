# 🚀 Quick Start - Memory Orchestrator Proxy

Guia rápido para colocar seu proxy funcionando com o Msty Studio em menos de 5 minutos.

## 📋 Pré-requisitos

```bash
# Versões necessárias
python --version  # Python 3.11+
node --version    # Node 18+ (para Graphiti MCP)

# Verifique se tem as API keys
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY  # Opcional
```

## ⚡ Setup Rápido

### 1. Clone e instale dependências

```bash
cd python-proxy
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate

pip install -r requirements.txt
```

### 2. Configure o .env

```bash
cp .env.example .env
```

Edite o `.env` e adicione **no mínimo**:

```bash
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
NEO4J_PASSWORD=sua-senha-neo4j
```

### 3. Rode o proxy

```bash
# Modo desenvolvimento (com reload)
python main.py

# Ou via uvicorn
uvicorn main:app --reload --port 8000
```

Você deve ver:

```
🚀 Starting Memory Orchestrator Proxy
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 4. Teste o health check

```bash
curl http://localhost:8000/health
```

Resposta esperada:

```json
{
  "status": "ok",
  "service": "memory-orchestrator-proxy",
  "components": {
    "graphiti": true,
    "neo4j": true,
    "openai": true
  }
}
```

## 🎨 Configure no Msty Studio

### Opção A: Via UI do Msty

1. Abra Msty Studio
2. Vá em `Settings > Model Providers`
3. Clique em `Add Custom Provider`
4. Configure:
   - **Name:** Memory Orchestrator
   - **Base URL:** `http://localhost:8000/v1`
   - **API Key:** Sua OpenAI key
   - **Models:** `gpt-4-memory`, `auto-route`, `claude-3-5-sonnet-memory`

### Opção B: Via arquivo de config

Crie ou edite `~/.msty/config.json`:

```json
{
  "providers": [
    {
      "name": "Memory Orchestrator",
      "base_url": "http://localhost:8000/v1",
      "api_key": "sua-openai-key",
      "models": [
        {
          "id": "gpt-4-memory",
          "name": "GPT-4 (with Memory)"
        },
        {
          "id": "auto-route",
          "name": "Auto-Select Best Model"
        }
      ]
    }
  ]
}
```

## 🧪 Teste a Integração

### No terminal:

```bash
curl -X POST http://localhost:8000/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -H "X-Persona: job-seeker" \\
  -d '{
    "model": "auto-route",
    "messages": [
      {"role": "user", "content": "Olá, tudo bem?"}
    ]
  }'
```

### No Msty Studio:

1. Selecione o modelo "GPT-4 (with Memory)"
2. Digite: "Olá, tudo bem?"
3. O proxy deve retornar uma resposta
4. Verifique os logs no terminal do proxy

## 📊 Monitore as Métricas

```bash
# Endpoint de métricas
curl http://localhost:8000/metrics

# Resposta
{
  "summary": {
    "total_requests": 15,
    "total_cost_usd": 0.0234,
    "avg_response_time_ms": 1234.56
  },
  "by_model": {
    "gpt-4": {"requests": 10, "cost_usd": 0.02},
    "gpt-4o-mini": {"requests": 5, "cost_usd": 0.0034}
  },
  "memory": {
    "total_memories_used": 45,
    "hit_rate": 68
  }
}
```

## 🎭 Use Personas

Adicione o header `X-Persona` para usar diferentes contextos:

```bash
curl -X POST http://localhost:8000/v1/chat/completions \\
  -H "X-Persona: developer" \\
  -d '{
    "model": "auto-route",
    "messages": [{"role": "user", "content": "Mostre meus projetos recentes"}]
  }'
```

**Personas disponíveis:**
- `default`: Uso geral
- `job-seeker`: Busca de emprego
- `developer`: Desenvolvimento/aprendizado
- `marketer`: Marketing e campanhas
- `researcher`: Pesquisa acadêmica

## 🧠 Testando o Router Standalone

Sem precisar do servidor, apenas o módulo router:

```bash
python example_usage.py
```

Isso vai rodar exemplos de:
- Conversa casual
- Recall de memórias
- Perguntas complexas
- Store de informações
- Classificação de intenções

## 🐛 Troubleshooting

### Erro: "OPENAI_API_KEY not found"

```bash
export OPENAI_API_KEY='sk-proj-...'
```

### Erro: "Neo4j connection refused"

Verifique se o Neo4j está rodando:

```bash
# Docker
docker ps | grep neo4j

# Se não estiver, rode:
docker run \\
  --name neo4j \\
  -p 7474:7474 -p 7687:7687 \\
  -e NEO4J_AUTH=neo4j/sua-senha \\
  neo4j:latest
```

### Erro: "MCP not reachable"

O proxy funciona sem MCP, mas sem memória persistente.

Para habilitar o Graphiti MCP:

```bash
# Instale
npm install -g @getzep/mcp-server-graphiti

# Configure no .env
GRAPHITI_MCP_COMMAND=npx @getzep/mcp-server-graphiti
GRAPHITI_MCP_ENABLED=true
```

### Logs não aparecem

Aumente o nível de log no `.env`:

```bash
LOG_LEVEL=debug
```

## 🚀 Próximos Passos

1. ✅ Configure personas personalizadas em `config.py`
2. ✅ Explore o dashboard web (em breve)
3. ✅ Integre com mais providers (Groq, Gemini, etc)
4. ✅ Configure alertas de custo
5. ✅ Implemente fallback para RAG vetorial

## 📚 Documentação Completa

- [README.md](README.md) - Visão geral do projeto
- [config.py](config.py) - Todas as configurações disponíveis
- [modules/router.py](modules/router.py) - Documentação do router
- [Msty Studio Docs](https://docs.msty.studio) - Docs oficiais do Msty

---

**Pronto! 🎉 Seu proxy está funcionando.**

Dúvidas? Abra uma issue ou consulte a documentação completa.
