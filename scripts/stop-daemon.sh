#!/bin/bash
# Stop the background memory proxy started via start-daemon.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="${ROOT_DIR}/logs"
PID_FILE="${LOG_DIR}/proxy.pid"

if [ ! -f "${PID_FILE}" ]; then
  echo "No PID file found at ${PID_FILE}. Proxy is not running?"
  exit 0
fi

PID="$(cat "${PID_FILE}")"
if kill -0 "${PID}" 2>/dev/null; then
  echo "Stopping memory proxy (PID ${PID})..."
  kill "${PID}"
  sleep 1
  if kill -0 "${PID}" 2>/dev/null; then
    echo "Force killing PID ${PID}..."
    kill -9 "${PID}"
  fi
else
  echo "Process ${PID} is not running."
fi

rm -f "${PID_FILE}"
echo "Memory proxy stopped."

