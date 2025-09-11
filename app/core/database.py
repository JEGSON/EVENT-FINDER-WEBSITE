"""SQLite connection helpers and FastAPI DB dependencies.

This module centralizes SQLite connection configuration, a contextmanager for
scripted sessions, a FastAPI dependency for request-scoped connections, and
database initialization (DDL and indexes).
"""

import sqlite3
from contextlib import contextmanager
import logging
from pathlib import Path
from typing import Iterator

from .config import settings


DB_PATH = Path(settings.database_path)


def _connect() -> sqlite3.Connection:
    """Create a SQLite connection with row factory configured."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db_session() -> Iterator[sqlite3.Connection]:
    """Context-managed DB session for scripts and CLIs.

    Commits on success, rolls back on exception, and always closes the
    connection.
    """
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_db() -> Iterator[sqlite3.Connection]:
    """FastAPI dependency yielding a DB connection.

    Request-scoped: commits on success, rolls back on exception, then closes.
    """
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _ensure_fts5(conn: sqlite3.Connection) -> None:
    """Create FTS5 virtual table and triggers if available.

    Attempts to create an external-content FTS5 table to index title and
    description. If FTS5 isn't compiled in, exits quietly.
    """
    cur = conn.cursor()
    try:
        cur.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS events_fts
            USING fts5(
              title,
              description,
              content='events',
              content_rowid='id'
            )
            """
        )
        # Triggers to keep FTS in sync
        cur.execute(
            """
            CREATE TRIGGER IF NOT EXISTS events_fts_ai AFTER INSERT ON events BEGIN
              INSERT INTO events_fts(rowid, title, description)
              VALUES (new.id, new.title, new.description);
            END;
            """
        )
        cur.execute(
            """
            CREATE TRIGGER IF NOT EXISTS events_fts_ad AFTER DELETE ON events BEGIN
              INSERT INTO events_fts(events_fts, rowid, title, description)
              VALUES('delete', old.id, old.title, old.description);
            END;
            """
        )
        cur.execute(
            """
            CREATE TRIGGER IF NOT EXISTS events_fts_au AFTER UPDATE ON events BEGIN
              INSERT INTO events_fts(events_fts, rowid, title, description)
              VALUES('delete', old.id, old.title, old.description);
              INSERT INTO events_fts(rowid, title, description)
              VALUES (new.id, new.title, new.description);
            END;
            """
        )
    except sqlite3.OperationalError as e:
        # If FTS5 is not available, ignore. Other errors bubble up.
        if 'fts5' in str(e).lower():
            logging.getLogger(__name__).info("SQLite FTS5 not available; continuing without full-text index")
            return
        raise


def init_db() -> None:
    """Create database file, schema, and useful indexes if missing."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                location TEXT NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
            )
            """
        )
        # Helpful indexes for search and sorting
        cur.execute("CREATE INDEX IF NOT EXISTS idx_events_date ON events(date)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_events_category ON events(LOWER(category))")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_events_location ON events(LOWER(location))")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_events_title ON events(LOWER(title))")
        _ensure_fts5(conn)
        conn.commit()
