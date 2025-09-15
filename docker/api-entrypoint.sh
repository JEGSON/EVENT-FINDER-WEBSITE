#!/usr/bin/env sh
set -eu

# Default port for local runs; Render provides $PORT
: "${PORT:=8001}"

# Ensure DB directory exists and is writable at runtime (handles mounted disks)
DB_PATH="${EVENTFINDER_DATABASE_PATH:-/data/event_finder.db}"
DB_DIR="$(dirname "$DB_PATH")"
mkdir -p "$DB_DIR" || true
chown -R 0:0 "$DB_DIR" || true
chmod -R 0777 "$DB_DIR" || true

exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"

