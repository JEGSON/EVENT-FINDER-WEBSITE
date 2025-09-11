#!/usr/bin/env sh
set -eu

mkdir -p /data

# Start FastAPI backend (port 8001)
uvicorn app.main:app --host 0.0.0.0 --port 8001 &
API_PID=$!

# Serve static site (port 8000) from /app
python -m http.server 8000 --directory /app &
WEB_PID=$!

cleanup() {
  kill "$API_PID" "$WEB_PID" 2>/dev/null || true
}
trap cleanup INT TERM

# Portable alternative to `wait -n`: poll both PIDs and exit when either dies
while :; do
  if ! kill -0 "$API_PID" 2>/dev/null; then
    echo "API process exited; shutting down web" >&2
    break
  fi
  if ! kill -0 "$WEB_PID" 2>/dev/null; then
    echo "Web process exited; shutting down API" >&2
    break
  fi
  sleep 1
done

cleanup

# Ensure both children have fully exited
wait "$API_PID" 2>/dev/null || true
wait "$WEB_PID" 2>/dev/null || true
