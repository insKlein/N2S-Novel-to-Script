#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

BACKEND_PORT="${N2S_BACKEND_PORT:-8000}"
FRONTEND_PORT="${N2S_FRONTEND_PORT:-3000}"
LOG_DIR="$ROOT_DIR/.run"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"
BACKEND_PID="$LOG_DIR/backend.pid"
FRONTEND_PID="$LOG_DIR/frontend.pid"

mkdir -p "$LOG_DIR"

is_listening() {
  lsof -iTCP:"$1" -sTCP:LISTEN -n -P >/dev/null 2>&1
}

ensure_python_deps() {
  if [ ! -x "$ROOT_DIR/.venv/bin/uvicorn" ]; then
    echo "首次准备 Python 环境..."
    python3 -m venv "$ROOT_DIR/.venv"
    "$ROOT_DIR/.venv/bin/python" -m pip install -r "$ROOT_DIR/requirements.txt"
  fi
}

ensure_frontend_deps() {
  if [ ! -x "$ROOT_DIR/frontend/node_modules/.bin/next" ]; then
    echo "首次准备前端依赖..."
    (cd "$ROOT_DIR/frontend" && npm install)
  fi
}

start_backend() {
  if is_listening "$BACKEND_PORT"; then
    echo "后端端口 $BACKEND_PORT 已有服务在运行，跳过启动。"
    return
  fi
  echo "启动后端：http://127.0.0.1:$BACKEND_PORT"
  nohup "$ROOT_DIR/.venv/bin/uvicorn" backend.app:app --port "$BACKEND_PORT" >"$BACKEND_LOG" 2>&1 &
  echo "$!" > "$BACKEND_PID"
}

start_frontend() {
  if is_listening "$FRONTEND_PORT"; then
    echo "前端端口 $FRONTEND_PORT 已有服务在运行，跳过启动。"
    return
  fi
  echo "启动前端：http://localhost:$FRONTEND_PORT"
  (
    cd "$ROOT_DIR/frontend"
    nohup env NEXT_PUBLIC_N2S_API_URL="http://127.0.0.1:$BACKEND_PORT" npm run dev -- --port "$FRONTEND_PORT" >"$FRONTEND_LOG" 2>&1 &
    echo "$!" > "$FRONTEND_PID"
  )
}

wait_for_url() {
  local url="$1"
  local name="$2"
  for _ in $(seq 1 30); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "$name 已就绪。"
      return
    fi
    sleep 1
  done
  echo "$name 启动较慢，请查看日志：$LOG_DIR" >&2
}

ensure_python_deps
ensure_frontend_deps
start_backend
start_frontend
wait_for_url "http://127.0.0.1:$BACKEND_PORT/api/health" "后端"
wait_for_url "http://localhost:$FRONTEND_PORT" "前端"

echo
echo "N2S 已启动： http://localhost:$FRONTEND_PORT"
echo "日志目录：$LOG_DIR"

if command -v open >/dev/null 2>&1; then
  open "http://localhost:$FRONTEND_PORT"
fi
