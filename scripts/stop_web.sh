#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$ROOT_DIR/.run"

stop_pid_file() {
  local file="$1"
  local name="$2"
  if [ -f "$file" ]; then
    local pid
    pid="$(cat "$file")"
    if kill -0 "$pid" >/dev/null 2>&1; then
      echo "停止 $name (PID $pid)"
      kill "$pid" || true
    fi
    rm -f "$file"
  fi
}

stop_pid_file "$LOG_DIR/backend.pid" "后端"
stop_pid_file "$LOG_DIR/frontend.pid" "前端"

echo "N2S Web 已停止。"
