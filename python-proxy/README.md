# 🧠 Memory Orchestrator Proxy (Python/FastAPI)

Proxy inteligente que se integra ao Msty Studio, mantendo memória persistente e roteando entre diferentes modelos de IA.

## 🎯 Características

- ✅ API compatível com OpenAI (`/v1/chat/completions`)
- ✅ Memória persistente com Graphiti + Neo4j
- ✅ Roteamento inteligente de modelos (GPT-4, Claude, etc)
- ✅ Sistema de personas com namespaces isolados
- ✅ Análise de intenção de prompts
- ✅ Enriquecimento automático de contexto
- ✅ Logging detalhado com custos e métricas
- ✅ Suporte a MCP tools

## 🚀 Quick Start

### Pré-requisitos

- Python 3.11+
- Neo4j rodando localmente ou na nuvem
- Graphiti MCP configurado
- API keys (OpenAI, Anthropic, etc)

### Instalação

```bash
cd python-proxy
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Configuração

```bash
cp .env.example .env
# Editar .env com suas credenciais
```

### Rodar

```bash
# Desenvolvimento
uvicorn main:app --reload --port 8000

# Produção
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📋 Estrutura do Projeto

```
python-proxy/
├── main.py                 # Entry point FastAPI
├── config.py              # Configurações e variáveis de ambiente
├── requirements.txt       # Dependências Python
├── .env.example          # Template de configuração
│
├── modules/
│   ├── intent_analyzer.py    # Análise de intenção do prompt
│   ├── memory_manager.py     # Integração com Graphiti
│   ├── model_router.py       # Roteamento inteligente de modelos
│   ├── prompt_enricher.py    # Enriquecimento de contexto
│   ├── persona_manager.py    # Sistema de personas
│   └── mcp_tools.py          # Ferramentas MCP
│
├── providers/
│   ├── openai_provider.py    # Client OpenAI
│   ├── anthropic_provider.py # Client Anthropic
│   └── base_provider.py      # Interface base
│
├── models/
│   ├── request_models.py     # Modelos Pydantic para requests
│   └── response_models.py    # Modelos Pydantic para responses
│
└── utils/
    ├── logger.py             # Sistema de logging
    ├── metrics.py            # Métricas e custos
    └── cache.py              # Cache de embeddings e queries
```

## 🔧 Configuração no Msty Studio

No Msty Studio, adicione um provider customizado:

```json
{
  "name": "Memory Orchestrator",
  "base_url": "http://localhost:8000/v1",
  "api_key": "sua-openai-key",
  "models": [
    "gpt-4-memory",
    "claude-3-5-sonnet-memory",
    "auto-route"
  ]
}
```

## 📊 Endpoints Disponíveis

### Chat Completions
```bash
POST /v1/chat/completions
```

### Health Check
```bash
GET /health
```

### Métricas
```bash
GET /metrics
```

### Memory Management
```bash
GET /memory/stats
POST /memory/add
POST /memory/search
```

## 🧪 Exemplo de Uso

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Persona: job-seeker" \
  -d '{
    "model": "auto-route",
    "messages": [
      {"role": "user", "content": "Quais empresas eu já apliquei?"}
    ]
  }'
```

## 🎭 Personas

Configure múltiplas personas em `config.py`:

```python
PERSONAS = {
    "job-seeker": {
        "namespaces": ["applications", "companies", "skills"],
        "default_model": "gpt-4",
        "memory_enabled": True
    },
    "developer": {
        "namespaces": ["code", "learning", "projects"],
        "default_model": "claude-3-5-sonnet",
        "memory_enabled": True
    }
}
```

## 📈 Logging e Métricas

Todos os requests são logados com:
- Tempo de resposta
- Custo estimado
- Tokens utilizados
- Memórias recuperadas
- Modelo selecionado

## 🔐 Segurança

- API keys armazenadas em `.env` (nunca comitar!)
- Validação de requests com Pydantic
- Rate limiting configurável
- CORS configurável para produção

## 🚦 Status do Projeto

- [x] Estrutura base
- [x] Endpoint OpenAI-compatible
- [x] Integração Graphiti
- [x] Roteamento de modelos
- [x] Sistema de personas
- [ ] Dashboard web
- [ ] Fallback RAG vetorial
- [ ] CLI standalone

## 📝 Licença

MIT
