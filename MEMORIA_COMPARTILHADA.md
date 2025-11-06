# Memória Compartilhada Entre Clientes 🔄

## 🎯 Problema

Por padrão, cada cliente (Msty, Terminal, etc.) usa um `user_id` diferente:

- **Msty**: Usa o IP ou um ID gerado
- **Terminal**: Usa `127.0.0.1` ou IP local
- **Resultado**: Memórias separadas 🔀

## ✅ Solução: User ID Fixo

### Configuração Atual

**Terminal (comando `ai`)** - Já configurado:
```bash
User ID: joao
Conversation ID: main
```

### Como Funciona

Todas as conversas com:
- `user_id = "joao"`
- `conversation_id = "main"`

Compartilham a **mesma memória**! 🎉

---

## 🔧 Configurar Outros Clientes

### Msty

1. **Configurar Headers Customizados**:
   ```
   X-User-ID: joao
   X-Conversation-ID: main
   ```

2. **Ou na URL** (se suportado):
   ```
   http://localhost:8000/chat/completions?user_id=joao
   ```

### Outros Clientes (cURL, Postman, etc.)

```bash
curl -X POST http://localhost:8000/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "X-User-ID: joao" \
  -H "X-Conversation-ID: main" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Qual é o nome do meu cachorro?"}]
  }'
```

---

## 📊 Estrutura de Memória

### User IDs Atuais

```
joao (novo, compartilhado)
  └── main (conversa principal)
      ├── Terminal ✅
      ├── Msty (quando configurado) ⏳
      └── Outros clientes (quando configurados) ⏳

127.0.0.1 (antigo, só terminal)
  └── default-127.0.0.1
      └── Conversas antigas do terminal
```

### No Redis

```bash
# Ver todas as memórias
redis-cli -n 0 KEYS "working_memory:*"

# Resultado:
working_memory:joao:default-joao          ← Nova (compartilhada)
working_memory:127.0.0.1:default-127.0.0.1 ← Antiga
```

---

## 🎮 Cenários de Uso

### Cenário 1: Memória Única (Atual)

**Todos os clientes compartilham:**
```
user_id: joao
conversation_id: main
```

**Vantagem**: Contexto completo em todos os clientes  
**Desvantagem**: Não separa por contexto/projeto

### Cenário 2: Memória por Projeto

**Terminal - Projeto A:**
```bash
# Modificar função ai:
X-User-ID: joao
X-Conversation-ID: projeto-a
```

**Msty - Projeto B:**
```
X-User-ID: joao
X-Conversation-ID: projeto-b
```

**Vantagem**: Contextos separados por projeto  
**Desvantagem**: Não compartilha entre projetos

### Cenário 3: Memória por Cliente

**Terminal:**
```
user_id: joao
conversation_id: terminal
```

**Msty:**
```
user_id: joao
conversation_id: msty
```

**Vantagem**: Histórico separado por ferramenta  
**Desvantagem**: Não compartilha contexto

---

## 🔄 Migrar Memórias Antigas

### Copiar memória antiga para nova:

```bash
# 1. Ver memória antiga
redis-cli -n 0 GET "working_memory:127.0.0.1:default-127.0.0.1"

# 2. Copiar para novo user_id
redis-cli -n 0 GET "working_memory:127.0.0.1:default-127.0.0.1" | \
  redis-cli -n 0 -x SET "working_memory:joao:default-joao"

# 3. Verificar
redis-cli -n 0 GET "working_memory:joao:default-joao"
```

### Mesclar memórias:

```bash
# Script para mesclar (avançado)
cd /Users/joaolucas/Desktop/Proxy\ Orchestrator/proxy-orchestrator
cat > merge_memories.py << 'EOF'
import redis
import json

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Ler memórias antigas
old_memory = r.get("working_memory:127.0.0.1:default-127.0.0.1")
new_memory = r.get("working_memory:joao:default-joao")

if old_memory and new_memory:
    old_turns = json.loads(old_memory)
    new_turns = json.loads(new_memory)
    
    # Mesclar
    merged = old_turns + new_turns
    
    # Limitar a 20 turnos
    merged = merged[-20:]
    
    # Salvar
    r.set("working_memory:joao:default-joao", json.dumps(merged))
    print(f"✅ Mescladas {len(old_turns)} + {len(new_turns)} = {len(merged)} conversas")
else:
    print("❌ Memórias não encontradas")
EOF

python merge_memories.py
```

---

## 📱 Comandos Úteis

### Ver todas as conversas de um usuário:
```bash
redis-cli -n 0 KEYS "working_memory:joao:*"
```

### Ver conversa específica:
```bash
redis-cli -n 0 GET "working_memory:joao:default-joao" | jq .
```

### Limpar memória de um usuário:
```bash
redis-cli -n 0 DEL "working_memory:joao:default-joao"
```

### Ver fatos extraídos (Tier 2):
```bash
redis-cli -n 1 KEYS "session:joao:*"
redis-cli -n 1 GET "session:joao:default-joao" | jq .
```

---

## 🎯 Recomendação

### Para Começar (Atual - Simples):
```
User ID: joao
Conversation ID: main
```
✅ Tudo compartilha a mesma memória

### Para Organização Avançada:
```
User ID: joao
Conversation ID: {projeto/contexto}
```

Exemplos:
- `projeto-memory-system`
- `trabalho-2024-11`
- `pessoal`
- `aprendizado-kubernetes`

---

## 🔍 Verificar Configuração Atual

```bash
# Ver última requisição
tail -5 /tmp/proxy_v3.log | grep "user_id"

# Ver memórias ativas
redis-cli -n 0 KEYS "working_memory:*"

# Testar
ai "Teste: qual meu user_id?"
```

---

## 💡 Dicas

1. **Escolha um padrão e mantenha**
   - Simples: `user_id=joao`, `conversation_id=main`
   - Por projeto: `user_id=joao`, `conversation_id=projeto-X`

2. **Configure todos os clientes igualmente**
   - Msty, Terminal, APIs devem usar os mesmos IDs

3. **Use nomes descritivos**
   - Ruim: `conv-1`, `user-abc`
   - Bom: `joao`, `projeto-memory`, `trabalho-q4`

4. **Monitore as memórias**
   ```bash
   # Ver quantas conversas
   redis-cli -n 0 KEYS "working_memory:*" | wc -l
   
   # Ver tamanho
   redis-cli -n 0 MEMORY USAGE "working_memory:joao:default-joao"
   ```

---

**Versão**: 1.0  
**Data**: 2025-11-05  
**Status**: ✅ Configurado com user_id fixo
