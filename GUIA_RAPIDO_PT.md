# Guia Rápido - AI com Memória 🧠

## 🎯 Como Usar

### No Terminal do Warp (Funciona!)

```bash
# Diga algo ao AI
ai "Meu nome é João e tenho um cachorro chamado Max"

# Pergunte depois
ai "Qual é o nome do meu cachorro?"
# ✅ Responde: "Max"

# Versão rápida (sem mostrar métricas)
ask "Como listar arquivos?"
```

### ❌ No Warp AI (Cmd+I) - NÃO Funciona

O chat do Warp AI (aquele que abre com Cmd+I) **ainda não suporta** endpoints customizados.

Por enquanto, use os comandos `ai` e `ask` no terminal!

---

## 💡 Exemplos Práticos

### Armazenar Informações

```bash
ai "Estou trabalhando no projeto de memória distribuída"
ai "Minha cor favorita é azul"
ai "Gosto de programar em Python"
```

### Recuperar Informações

```bash
ai "Em que projeto estou trabalhando?"
# ✅ Responde com o projeto

ai "Qual minha cor favorita?"
# ✅ Responde "azul"

ai "Quais linguagens eu gosto?"
# ✅ Responde "Python"
```

### Perguntas Profundas (usa todas as camadas)

```bash
ai "Lembra quando conversamos sobre meus projetos?"
ai "Compare minhas preferências ao longo do tempo"
```

---

## 🎮 Comandos Disponíveis

| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `ai "pergunta"` | Versão completa com métricas | `ai "Qual meu nome?"` |
| `ask "pergunta"` | Versão rápida sem métricas | `ask "2+2?"` |
| `aiq "pergunta"` | Alias para ask | `aiq "Como listar?"` |
| `memcheck` | Verificar status do proxy | `memcheck` |

---

## 📊 Como Funciona

### 3 Camadas de Memória

**Camada 1** (90% das consultas - rápida)
```bash
ask "Olá"
ask "Obrigado"
```
→ Últimas 10 conversas (~200 tokens)

**Camada 2** (8% das consultas - fatos)
```bash
ai "Qual meu nome?"
ai "O que eu gosto?"
```
→ Últimas 15 conversas + fatos extraídos (~400 tokens)

**Camada 3** (2% das consultas - completa)
```bash
ai "Lembra quando falamos sobre...?"
ai "Compare minhas preferências"
```
→ Todas as camadas + grafo de conhecimento (~1000 tokens)

---

## 🔍 Monitorar Memória

### Ver uso em tempo real
```bash
tail -f /tmp/proxy_v3.log | grep tier_level
```

### Ver economia de tokens
```bash
grep "total_cost_estimate" /tmp/proxy_v3.log | \
  awk '{sum+=$NF; count++} END {print "Média:", sum/count, "tokens"}'
```

### Ver distribuição de camadas
```bash
grep "tier_level" /tmp/proxy_v3.log | \
  awk '{print $NF}' | sort | uniq -c
```

Esperado: ~90% Camada 1, ~8% Camada 2, ~2% Camada 3

---

## 🔧 Gerenciamento

### Verificar Status
```bash
memcheck
```

### Limpar Memórias

```bash
# Limpar conversas (Camada 1)
redis-cli -n 0 FLUSHDB

# Limpar fatos (Camada 2)
redis-cli -n 1 FLUSHDB

# Limpar tudo
redis-cli FLUSHALL
```

### Iniciar Proxy (se não estiver rodando)
```bash
cd ~/Desktop/Proxy\ Orchestrator/proxy-orchestrator/python-proxy
python main.py
```

---

## 💰 Economia

### Antes (OpenAI direto)
- Média: 1000 tokens por consulta
- Sem memória
- Sem contexto

### Depois (Com Proxy)
- Média: 232 tokens por consulta
- Memória completa entre sessões
- Contexto inteligente
- **77% de economia!**

---

## 🐛 Problemas Comuns

### "command not found: ai"
```bash
source ~/.zshrc
```

### "Connection refused"
```bash
# Iniciar proxy
cd ~/Desktop/Proxy\ Orchestrator/proxy-orchestrator/python-proxy
python main.py &
```

### Memória não funciona
```bash
# Verificar logs
tail -50 /tmp/proxy_v3.log

# Verificar Redis
redis-cli PING

# Verificar proxy
memcheck
```

---

## 🎓 Casos de Uso

### 1. Assistente Pessoal
```bash
ai "Minha reunião é às 15h"
# Depois...
ai "A que horas é minha reunião?"
```

### 2. Aprendizado
```bash
ai "Explica Kubernetes pra mim"
# Depois...
ai "O que discutimos sobre Kubernetes?"
```

### 3. Tracking de Trabalho
```bash
ai "Hoje corrigi o bug de memória"
ai "Implementei injeção progressiva"
# Depois...
ai "O que fiz hoje?"
```

---

## ⚠️ Importante

### ✅ FUNCIONA:
- Terminal do Warp com comando `ai` ou `ask`
- Memória persistente
- Economia de tokens

### ❌ NÃO FUNCIONA (ainda):
- Warp AI (Cmd+I)
- Chat interface do Warp
- Aguardando suporte a endpoints customizados

---

## 🚀 Teste Agora!

```bash
# 1. Diga algo
ai "Meu nome é João"

# 2. Pergunte
ai "Qual é meu nome?"

# 3. Veja funcionando!
# Resposta: "Seu nome é João"
```

---

**Versão**: 1.0  
**Data**: 2025-11-05  
**Status**: ✅ Funcionando!

## Referência Rápida

```bash
# Perguntar
ai "sua pergunta"

# Rápido
ask "sua pergunta"

# Status
memcheck

# Logs
tail -f /tmp/proxy_v3.log

# Limpar
redis-cli -n 0 FLUSHDB  # Camada 1
redis-cli -n 1 FLUSHDB  # Camada 2
```

**Aproveite seu AI com memória! 🎉**
