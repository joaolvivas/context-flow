# ContextFlow Memory System - Guia de Uso

## 🚀 Início Rápido

### Comando Único
```bash
bash start_memory_system.sh
```

Isso inicia:
- 🧠 Memory Proxy (porta 8000)
- 📡 Graphiti Bridge (porta 5001)

## ⚙️ Auto-Start (Configurado!)

O sistema está configurado para **iniciar automaticamente** quando você ligar o Mac.

### Gerenciar Auto-Start

**Desabilitar auto-start:**
```bash
launchctl unload ~/Library/LaunchAgents/com.contextflow.memory.plist
```

**Reabilitar auto-start:**
```bash
launchctl load ~/Library/LaunchAgents/com.contextflow.memory.plist
```

**Verificar status:**
```bash
launchctl list | grep contextflow
```

## 🔍 Verificar Status

**Health checks:**
```bash
curl http://localhost:8000/health | jq
curl http://localhost:5001/health | jq
```

**Ver logs:**
```bash
# Proxy
tail -f /tmp/proxy_v3.log

# Bridge
tail -f /tmp/http_wrapper.log

# Startup (LaunchAgent)
tail -f /tmp/contextflow_startup.log
```

## 🛑 Parar Serviços

```bash
pkill -f 'main.py|graphiti_http_bridge'
```

## 🔧 Testar Memória

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "X-User-Id: lucas-ai" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Quem sou eu?"}]
  }' | jq -r '.choices[0].message.content'
```

## 📍 Endpoints

- **Proxy**: http://localhost:8000
  - `/health` - Status
  - `/v1/chat/completions` - OpenAI-compatible endpoint

- **Bridge**: http://localhost:5001
  - `/health` - Status
  - `/mcp/search` - Search memories
  - `/mcp/store` - Store memories

## 🔑 Configuração Msty

No Msty, configure:
- **Base URL**: `http://localhost:8000/v1`
- **API Key**: Sua OpenAI API key
- **Model**: `gpt-4o-mini` ou `gpt-4o`

O sistema injeta automaticamente memórias do Graphiti!

## 🧹 Troubleshooting

**Serviços não iniciam:**
```bash
# Check logs
cat /tmp/contextflow_startup_error.log

# Restart manually
bash start_memory_system.sh
```

**Porta já em uso:**
```bash
# Kill existing processes
pkill -9 -f 'main.py|graphiti_http_bridge'
sleep 2
bash start_memory_system.sh
```

**Memórias não aparecem:**
- Verifique se o user_id está correto: `lucas-ai`
- Check bridge logs: `tail /tmp/http_wrapper.log`
- Teste direto: `curl http://localhost:5001/mcp/search -d '{"query":"test","user_id":"lucas-ai","limit":5}'`

## 📊 Arquitetura

```
Msty/App
    ↓
Memory Proxy :8000 (python-proxy/main.py)
    ↓ busca memórias
Graphiti Bridge :5001 (src/contextflow/bridges/graphiti_http_bridge.py)
    ↓ NODE_HYBRID_SEARCH_RRF + search()
Graphiti + Neo4j AuraDB
    ↓
Entity Nodes (biografias) + Facts (relacionamentos)
```

## 🎯 Features

✅ **Node + Edge Search**: Retorna entity summaries (biografias completas) + facts  
✅ **3-Tier Memory**: Working + Session + Graphiti  
✅ **Auto-Start**: LaunchAgent configurado  
✅ **One-Command**: `bash start_memory_system.sh`  
✅ **OpenAI Compatible**: Funciona com qualquer cliente OpenAI

## 📝 Logs Importantes

- Busca retornando nodes: `✓ Search returned 3 results (3 nodes, 0 facts)`
- Significa que está funcionando corretamente!

---

**Versão**: 3.1.0  
**Última atualização**: 2025-11-06  
**Status**: ✅ Funcionando e testado
