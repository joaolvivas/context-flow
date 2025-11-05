# 🎨 Integração com Msty Studio

Guia completo de como integrar o Memory Orchestrator Proxy com o Msty Studio para ter memória persistente em todas as suas conversas.

## 🎯 Por que usar este proxy com Msty?

| Recurso | Msty Studio Padrão | Msty + Memory Proxy |
|---------|-------------------|---------------------|
| Memória | Por sessão | Persistente para sempre |
| Multi-modelo | ✅ Manual | ✅ Roteamento automático |
| Contexto | Knowledge Stacks (estático) | Grafo dinâmico (evolui) |
| Personas | ❌ | ✅ job-seeker, developer, etc |
| Custos | Não rastreia | ✅ Tracking completo |

## 🔧 Setup no Msty Studio

### Método 1: Via UI (Recomendado)

#### Passo 1: Inicie o proxy

```bash
cd python-proxy
source venv/bin/activate
python main.py
```

Aguarde ver:

```
🚀 Starting Memory Orchestrator Proxy
INFO:     Uvicorn running on http://0.0.0.0:8000
```

#### Passo 2: Abra Msty Studio

#### Passo 3: Adicione o provider customizado

1. `Settings > Remote Model Providers`
2. Clique em `Add New Provider`
3. Selecione `OpenAI Compatible`
4. Preencha:
   - **Nome:** `Memory Orchestrator`
   - **API Endpoint:** `http://localhost:8000/v1`
   - **API Key:** Sua chave OpenAI real
5. Clique em `Fetch Models` (ou adicione manualmente)

#### Passo 4: Adicione modelos manualmente

Se `Fetch Models` não funcionar, adicione manualmente:

| Model ID | Nome Exibido | Contexto |
|----------|-------------|----------|
| `gpt-4-memory` | GPT-4 (with Memory) | 128k |
| `gpt-4o-memory` | GPT-4o (with Memory) | 128k |
| `gpt-4o-mini-memory` | GPT-4o Mini (with Memory) | 128k |
| `claude-3-5-sonnet-memory` | Claude 3.5 Sonnet (with Memory) | 200k |
| `auto-route` | Auto-Select Best Model | 128k |

#### Passo 5: Salve e teste

1. Crie um novo chat
2. Selecione `GPT-4 (with Memory)` no selector
3. Digite: "Olá, me chamo João e sou desenvolvedor"
4. Em um **novo chat**, digite: "Qual é o meu nome?"
5. O proxy deve lembrar que você é João! 🎉

### Método 2: Via Arquivo de Config

Edite `~/.msty/workspaces/<workspace>/config.json`:

```json
{
  "remote_providers": [
    {
      "id": "memory-orchestrator",
      "name": "Memory Orchestrator",
      "type": "openai_compatible",
      "base_url": "http://localhost:8000/v1",
      "api_key": "your-openai-key-here",
      "models": [
        {
          "id": "gpt-4-memory",
          "name": "GPT-4 (with Memory)",
          "context_length": 128000,
          "supports_streaming": true,
          "supports_functions": true
        },
        {
          "id": "auto-route",
          "name": "Auto-Select Best Model",
          "context_length": 128000,
          "supports_streaming": true
        }
      ]
    }
  ]
}
```

Reinicie o Msty Studio.

## 🎭 Usando Personas no Msty

Personas permitem contextos isolados para diferentes atividades.

### Ativar persona via Model Options

No Msty, ao usar um modelo com memória:

1. Clique em ⚙️ (Model Options)
2. Em `Extra Model Parameters`, adicione:

```json
{
  "persona": "job-seeker"
}
```

### Personas Disponíveis

| Persona | Uso | Namespaces |
|---------|-----|-----------|
| `default` | Uso geral | general |
| `job-seeker` | Busca de emprego | applications, companies, skills |
| `developer` | Desenvolvimento | code, learning, projects |
| `marketer` | Marketing | campaigns, metrics, clients |
| `researcher` | Pesquisa | papers, notes, experiments |

### Exemplo de Workflow

**Contexto: Busca de Emprego**

```json
{
  "persona": "job-seeker"
}
```

No chat:

```
Você: Apliquei para a vaga de Senior Engineer na Vercel hoje.
AI: ✅ Registrado! Boa sorte com a Vercel.

[Novo chat, dias depois]

Você: Quais empresas já apliquei essa semana?
AI: Você aplicou para:
     - Vercel (Senior Engineer) - 3 dias atrás
     - Linear (Growth Engineer) - 1 dia atrás
```

**Contexto: Desenvolvimento**

```json
{
  "persona": "developer"
}
```

No chat:

```
Você: Estou estudando FastAPI para criar APIs REST.
AI: Legal! FastAPI é excelente para APIs performáticas.

[Novo chat]

Você: Qual framework Python eu estava estudando?
AI: Você mencionou estar estudando FastAPI para criar APIs REST.
```

## 🔍 Recursos Avançados

### 1. Roteamento Automático de Modelos

Use `auto-route` para deixar o proxy escolher:

```json
{
  "model": "auto-route",
  "task_hint": "quick_answer"  // Opcional
}
```

Task hints disponíveis:
- `quick_answer`: Usa GPT-4o Mini (rápido e barato)
- `deep_analysis`: Usa Claude 3.5 Sonnet (raciocínio)
- `code_generation`: Usa GPT-4 (melhor para código)
- `summarize`: Usa Claude (ótimo para síntese)

### 2. Controle de Memória

Desabilitar memória temporariamente:

```json
{
  "memory_enabled": false
}
```

Buscar em namespaces específicos:

```json
{
  "memory_namespaces": ["applications", "interviews"]
}
```

Desabilitar armazenamento automático:

```json
{
  "auto_store_memory": false
}
```

### 3. Headers Customizados

O Msty permite passar headers customizados (se configurado):

```
X-Persona: developer
X-Memory-Namespaces: code,projects
```

## 📊 Monitorando Uso

### Métricas em Tempo Real

Abra em um navegador:

```
http://localhost:8000/metrics
```

Você verá:

```json
{
  "summary": {
    "total_requests": 127,
    "total_cost_usd": 2.34,
    "avg_response_time_ms": 892.45
  },
  "by_model": {
    "gpt-4": {
      "requests": 45,
      "tokens_input": 12450,
      "tokens_output": 8320,
      "cost_usd": 1.87
    },
    "gpt-4o-mini": {
      "requests": 82,
      "cost_usd": 0.47
    }
  },
  "by_persona": {
    "job-seeker": 67,
    "developer": 43,
    "default": 17
  },
  "memory": {
    "total_memories_used": 234,
    "requests_with_memory": 89,
    "hit_rate": 70.08
  }
}
```

### Logs Estruturados

No terminal onde o proxy roda, você vê logs em JSON:

```json
{
  "event": "request_received",
  "request_id": "abc123",
  "persona": "job-seeker",
  "model": "gpt-4-memory",
  "message_count": 1
}

{
  "event": "memory_retrieval",
  "request_id": "abc123",
  "memories_found": 3,
  "retrieval_time_ms": 145.23
}

{
  "event": "response_sent",
  "request_id": "abc123",
  "model": "gpt-4",
  "total_time_ms": 1234.56,
  "cost_usd": 0.0123,
  "memories_used": 3
}
```

## 🎨 Dicas de UX no Msty

### 1. Crie workspaces separados

- **Workspace "Job Search"**: Use persona `job-seeker`
- **Workspace "Development"**: Use persona `developer`
- **Workspace "Marketing"**: Use persona `marketer`

### 2. Use Split Chats

Abra múltiplos chats lado a lado:
- Chat 1: `GPT-4 (with Memory)` - Suas perguntas
- Chat 2: `GPT-4o Mini (standard)` - Comparação sem memória

### 3. Configure Model Defaults

Em cada workspace, defina:
- Default model: `auto-route`
- Extra params:

```json
{
  "persona": "job-seeker",
  "memory_enabled": true
}
```

## 🐛 Troubleshooting

### Erro: "Connection refused"

O proxy não está rodando. Inicie:

```bash
python main.py
```

### Erro: "Invalid API key"

A chave OpenAI configurada no Msty deve ser a **real**, não uma placeholder.

### Memória não funciona

Verifique:

1. Graphiti MCP está configurado?

```bash
echo $GRAPHITI_MCP_ENABLED
# Deve retornar: true
```

2. Neo4j está rodando?

```bash
docker ps | grep neo4j
```

3. Logs do proxy mostram erros?

```bash
# Olhe por "memory_retrieval_error" nos logs
```

### Respostas muito lentas

1. Desabilite memória para queries simples:

```json
{
  "memory_enabled": false
}
```

2. Use `gpt-4o-mini-memory` para respostas mais rápidas

3. Reduza `MEMORY_SEARCH_LIMIT` no `.env`:

```bash
MEMORY_SEARCH_LIMIT=3  # Padrão: 10
```

## 🚀 Próximos Passos

1. ✅ Configure personas personalizadas
2. ✅ Popule o grafo com suas informações
3. ✅ Explore diferentes modelos
4. ✅ Monitore custos e otimize
5. ✅ Compartilhe feedback!

## 📚 Recursos

- [QUICKSTART.md](QUICKSTART.md) - Setup inicial
- [README.md](README.md) - Documentação completa
- [Msty Docs](https://docs.msty.studio) - Docs oficiais do Msty
- [OpenAI API Docs](https://platform.openai.com/docs/api-reference)

---

**Dúvidas?** Abra uma issue no repositório ou consulte a documentação.
