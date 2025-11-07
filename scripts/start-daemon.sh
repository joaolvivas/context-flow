#!/bin/bash
# Start the memory proxy as a background service (24/7 mode)

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="${ROOT_DIR}/logs"
PROXY_DIR="${ROOT_DIR}/python-proxy"
VENV_DIR="${PROXY_DIR}/venv"
PID_FILE="${LOG_DIR}/proxy.pid"
LOG_FILE="${LOG_DIR}/proxy.log"

mkdir -p "${LOG_DIR}"

info() {
  printf "\033[0;34m%s\033[0m\n" "$1"
}

success() {
  printf "\033[0;32m%s\033[0m\n" "$1"
}

warn() {
  printf "\033[0;33m%s\033[0m\n" "$1"
}

# 1) Ensure Redis Stack is running (for LangMem persistence)
if ! docker ps --format '{{.Names}}' | grep -qw 'redis-stack'; then
  if docker ps -a --format '{{.Names}}' | grep -qw 'redis-stack'; then
    info "Starting existing redis-stack container..."
    docker start redis-stack >/dev/null
  else
    info "Launching redis-stack container (first run)..."
    docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 redis/redis-stack:latest >/dev/null
    success "redis-stack container created."
  fi
else
  info "redis-stack already running."
fi

# 2) Prepare Python environment
if [ ! -d "${VENV_DIR}" ]; then
  info "Creating virtual environment..."
  python3 -m venv "${VENV_DIR}"
  source "${VENV_DIR}/bin/activate"
  pip install --upgrade pip
  pip install -r "${PROXY_DIR}/requirements.txt"
else
  source "${VENV_DIR}/bin/activate"
fi

# 3) Avoid duplicate processes
if [ -f "${PID_FILE}" ]; then
  if kill -0 "$(cat "${PID_FILE}")" 2>/dev/null; then
    warn "Memory proxy already running (PID $(cat "${PID_FILE}"))."
    exit 0
  else
    warn "Removing stale PID file (${PID_FILE})."
    rm -f "${PID_FILE}"
  fi
fi

# 4) Start the proxy with nohup
cd "${PROXY_DIR}"
export PYTHONPATH="${ROOT_DIR}/src:${PYTHONPATH:-}"

info "Starting memory proxy in background..."
nohup uvicorn main:app --host 0.0.0.0 --port 8000 >> "${LOG_FILE}" 2>&1 &
PROXY_PID=$!
echo "${PROXY_PID}" > "${PID_FILE}"

success "Memory proxy started (PID ${PROXY_PID}). Logs: ${LOG_FILE}"

