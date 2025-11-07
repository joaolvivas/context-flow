## Reboot Checklist

Passo a passo para reativar o Proxy/Agente após reiniciar o Mac.

### 1. Abrir terminal
Qualquer shell (Warp, Terminal, iTerm, etc.).

### 2. Subir Redis Stack
```bash
docker start redis-stack
# Se for a primeira vez:
# docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 redis/redis-stack:latest
```

### 3. Iniciar o proxy/agente em background
```bash
cd ~/Desktop/"Proxy Orchestrator"/proxy-orchestrator
./scripts/start-daemon.sh
```
- Cria/usa `venv`, liga `uvicorn`, loga em `logs/proxy.log`.

### 4. Validar serviço
```bash
curl http://localhost:8000/health
curl http://localhost:8000/v1/memory/peek
```
Deve retornar 200 e mostrar Tier 1/2/3 com perfil seed.

### 5. Configurar Msty (se necessário)
- Base URL: `http://localhost:8000/v1`
- Use sua OpenAI/Claude API key como sempre.

### 6. Encerrar manualmente (opcional)
```bash
./scripts/stop-daemon.sh
```

### Automação opcional
Para iniciar no boot do macOS, crie um serviço `launchctl` apontando para `scripts/start-daemon.sh`.

