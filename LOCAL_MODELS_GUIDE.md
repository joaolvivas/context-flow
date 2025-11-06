# Usando Modelos Locais com ContextFlow

O proxy ContextFlow é **OpenAI-compatible**, então funciona com QUALQUER modelo local que exponha uma API compatível!

---

## 🌟 Opção 1: Ollama (RECOMENDADO)

### Por que Ollama?
- ✅ Instalação simples (via Homebrew)
- ✅ CLI poderoso
- ✅ Modelos otimizados (quantizados)
- ✅ OpenAI-compatible API
- ✅ Roda bem no Mac (ARM/Intel)

### Instalação
```bash
brew install ollama
ollama serve  # Inicia o servidor
```

### Modelos Recomendados

#### Para seu MacBook Air (8GB RAM estimado):

**Qwen 2.5 3B** (Melhor escolha! 🎯)
```bash
ollama pull qwen2.5:3b
```
- RAM: ~3GB
- Qualidade: Excelente para o tamanho
- Velocidade: Muito rápida
- Multilingual: Português nativo!

**Llama 3.2 3B**
```bash
ollama pull llama3.2:3b
```
- RAM: ~3GB
- Qualidade: Boa
- Meta oficial

**Qwen 2.5 7B** (Se tiver 16GB+ RAM)
```bash
ollama pull qwen2.5:7b
```
- RAM: ~8GB
- Qualidade: Próxima de GPT-3.5
- Melhor contexto longo

### Configurar no Msty

1. Abrir Msty
2. Adicionar provedor:
   - Nome: `Ollama Local`
   - Base URL: `http://localhost:11434/v1`
   - API Key: `ollama` (qualquer coisa)
   - Model: `qwen2.5:3b`

3. **Com ContextFlow Memory**:
   - Base URL: `http://localhost:8000/v1`
   - API Key: `ollama` (será passada para Ollama)
   - Model: `qwen2.5:3b`
   - Header: `X-Provider-URL: http://localhost:11434/v1`

---

## 🎨 Opção 2: LM Studio

### Por que LM Studio?
- ✅ GUI intuitiva
- ✅ Modelos pré-configurados
- ✅ Fácil gerenciar RAM/GPU

### Setup
1. Download: https://lmstudio.ai
2. Baixar modelo: `TheBloke/Mistral-7B-Instruct-v0.2-GGUF`
3. Start Server (porta 1234)

### Configurar no Msty com Memory
```
Base URL: http://localhost:8000/v1
API Key: lmstudio
Header: X-Provider-URL: http://localhost:1234/v1
```

---

## 📊 Comparação de Performance

### Com ContextFlow Memory:

| Model | RAM | Speed | Quality | Cost | Context |
|-------|-----|-------|---------|------|---------|
| **Qwen 2.5 3B** | 3GB | ⚡⚡⚡ | ⭐⭐⭐⭐ | $0 | 32K |
| **Llama 3.2 3B** | 3GB | ⚡⚡⚡ | ⭐⭐⭐ | $0 | 128K |
| **Qwen 2.5 7B** | 8GB | ⚡⚡ | ⭐⭐⭐⭐⭐ | $0 | 128K |
| **GPT-4o-mini** | Cloud | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | $32/yr | 128K |

### Tokens Esperados com Memory

Com ContextFlow adicionando ~3K tokens de memória:
- Input: 3,500 tokens (memoria + query)
- Output: 500-1000 tokens
- **Total: ~4-5K tokens/request**

**Veredito**: Modelos 3B conseguem lidar tranquilamente! O context de 32K é mais que suficiente.

---

## 🎯 Configuração Recomendada para Você

### Setup Híbrido (Melhor dos 2 mundos!)

**Msty Profile 1: Local (Rápido e Grátis)**
```
Name: Local + Memory
Base URL: http://localhost:8000/v1
Model: qwen2.5:3b
Header: X-Provider-URL: http://localhost:11434/v1
Use: Perguntas rápidas, testes
```

**Msty Profile 2: Cloud (Máxima Qualidade)**
```
Name: GPT-4o + Memory
Base URL: http://localhost:8000/v1
Model: gpt-4o-mini
API Key: sk-...
Use: Perguntas importantes, escrita
```

---

## 🚀 Quick Start com Ollama

```bash
# 1. Instalar Ollama
brew install ollama

# 2. Baixar modelo
ollama pull qwen2.5:3b

# 3. Testar direto
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:3b",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# 4. Testar com ContextFlow Memory
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ollama" \
  -H "X-User-Id: lucas-ai" \
  -H "X-Provider-URL: http://localhost:11434/v1" \
  -d '{
    "model": "qwen2.5:3b",
    "messages": [{"role": "user", "content": "Quem sou eu?"}]
  }'
```

---

## 💡 Dicas de Uso

### Quando usar Local:
- ✅ Testes e desenvolvimento
- ✅ Queries rápidas e simples
- ✅ Privacidade total
- ✅ Experimentação

### Quando usar Cloud (GPT-4o):
- ✅ Escrita importante
- ✅ Raciocínio complexo
- ✅ Multilingual avançado
- ✅ Quando precisa da melhor qualidade

### Economias:
- 90% queries em local: **$3.28/ano** (vs $32.85)
- 100% local: **$0/ano** 🎉

---

## 🔧 Troubleshooting

### Ollama não conecta
```bash
# Verificar se está rodando
ollama list

# Iniciar servidor
ollama serve
```

### Modelo lento
- Usar modelo menor (3B ao invés de 7B)
- Fechar outras apps
- Verificar se está usando GPU (Mac: Metal)

### Out of memory
```bash
# Usar modelo quantizado
ollama pull qwen2.5:3b-q4_0  # Ainda menor
```

### Qualidade baixa
- Testar Qwen 2.5 (melhor que Llama para PT)
- Aumentar context window no Ollama
- Considerar modelo 7B se tiver RAM

---

## 📈 Próximos Passos

1. **Instalar Ollama**: `brew install ollama`
2. **Baixar Qwen**: `ollama pull qwen2.5:3b`
3. **Testar direto**: `ollama run qwen2.5:3b "Olá!"`
4. **Configurar Msty**: Base URL para `http://localhost:8000/v1`
5. **Warm-up memory**: `bash warm_up_memory.sh`
6. **Testar**: "Quem sou eu?" no Msty

---

**Recomendação Final**: Comece com **Qwen 2.5 3B** via Ollama. É rápido, gratuito, e surpreendentemente bom com suas memórias do ContextFlow! 🚀

Se precisar de mais qualidade em queries específicas, mantenha GPT-4o-mini como backup.
