# Multi-process container: FastAPI backend (uvicorn) + static site server
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    EVENTFINDER_DATABASE_PATH=/data/event_finder.db

WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app
COPY assets ./assets
COPY index.html ./
COPY events.html ./
COPY event-detail.html ./
COPY about.html ./

# Add entrypoint script
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && useradd -m appuser \
    && mkdir -p /data \
    && chown -R appuser:appuser /data

VOLUME ["/data"]

EXPOSE 8000 8001

USER appuser

ENTRYPOINT ["/entrypoint.sh"]
