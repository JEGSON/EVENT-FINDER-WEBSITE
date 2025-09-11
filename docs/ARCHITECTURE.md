# Architecture Overview

Event Finder is a small, layered FastAPI + SQLite service with a static frontend.

## Backend (FastAPI)

- `app/main.py`: app factory, CORS, routers, `/health` and `/` redirect.
- `app/core/config.py`: runtime config from env/`.env` using pydantic-settings.
- `app/core/database.py`: SQLite connection helpers, FastAPI dependency, DDL init.
- `app/schemas/event.py`: Pydantic models/enums and validators.
- `app/repositories/events.py`: SQL queries for CRUD/search with sorting and paging.
- `app/api/routes/events.py`: HTTP endpoints orchestrating repo calls and responses.
- `scripts/seed.py`: development seeder.

### Request lifecycle

1. Request hits a route in `app/api/routes/...`.
2. A request-scoped DB connection is injected via `Depends(get_db)`.
3. Route builds an `EventQuery` (for list) or validates `EventCreate/EventUpdate`.
4. Repository executes SQL and maps rows to `EventOut` via `row_factory`.
5. Response is serialized by FastAPI; list route sets `X-Total-Count`.

### Data model (SQLite)

```\
CREATE TABLE events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  description TEXT,
  location TEXT NOT NULL,
  category TEXT NOT NULL,
  date TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
```

Indexes: by `date`, `LOWER(category)`, `LOWER(location)`, `created_at`, `LOWER(title)`

Full‑text search (FTS5): If the local SQLite build supports FTS5, an external‑content
virtual table `events_fts` indexes `title` and `description`, with triggers to keep
it in sync. The API transparently prefers FTS for `q=` searches and falls back to
`LIKE` when unavailable.

## Frontend (Static)

- Pages: `index.html`, `events.html`, `event-detail.html`, `about.html`
- Assets: `assets/css` uses CSS cascade layers:
  - `base`: tokens and resets
  - `layout`: page structure
  - `components`: buttons, forms, cards, badges, etc.
  - `theme`: ambient backgrounds, glassmorphism
  - `utilities`: helpers like `sr-only`
- JS fetches the API at `http://127.0.0.1:8001/api` (fallback from `localhost`).
- Pagination controls read `X-Total-Count` and render pages.

## Configuration

Environment variables (prefix `EVENTFINDER_`), e.g. `EVENTFINDER_DATABASE_PATH`.
Values can be placed in a local `.env` for development.
