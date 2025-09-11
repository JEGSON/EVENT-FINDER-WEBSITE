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

wait -n "$API_PID" "$WEB_PID"

