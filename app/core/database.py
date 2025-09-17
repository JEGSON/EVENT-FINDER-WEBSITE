"""SQLite connection helpers and FastAPI DB dependencies.

This module centralizes SQLite connection configuration, a contextmanager for
scripted sessions, a FastAPI dependency for request-scoped connections, and
database initialization (DDL and indexes).
"""

import os
import sqlite3
import time
from contextlib import contextmanager
import logging
from pathlib import Path
from typing import Iterator

from .config import settings


DB_PATH = Path(settings.database_path)


def _connect() -> sqlite3.Connection:
    """Create a SQLite connection with sensible defaults for web apps.

    - ``row_factory`` returns dict-like rows
    - ``busy_timeout`` prevents immediate "database is locked" errors
    - ``journal_mode=WAL`` improves concurrent readers
    - ``synchronous=NORMAL`` balances durability/perf for web traffic
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA foreign_keys=ON")
    except sqlite3.Error:
        # Pragmas are best-effort and platform dependent; ignore failures
        pass
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


def _create_schema(conn: sqlite3.Connection) -> None:
    """Create core tables and indexes."""
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


def _integrity_ok(conn: sqlite3.Connection) -> bool:
    """Return True if PRAGMA quick_check reports OK, else False."""
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA quick_check")
        row = cur.fetchone()
        return bool(row and str(row[0]).lower() == "ok")
    except sqlite3.DatabaseError:
        return False


def init_db() -> None:
    """Create database and schema; optionally auto-repair if corrupted.

    If ``EVENTFINDER_DB_AUTOREPAIR`` is set to a truthy value ("1", "true",
    "yes"), a corrupted SQLite file will be backed up and recreated.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    need_repair = False
    if DB_PATH.exists():
        try:
            with _connect() as c:
                need_repair = not _integrity_ok(c)
        except sqlite3.DatabaseError:
            need_repair = True

    if need_repair and str(os.getenv("EVENTFINDER_DB_AUTOREPAIR", "")).lower() in {"1", "true", "yes"}:
        try:
            backup = DB_PATH.with_name(DB_PATH.name + f".bak-{time.strftime('%Y%m%d%H%M%S')}")
            DB_PATH.rename(backup)
        except Exception:
            # If we cannot rename, fall back to removing the corrupted file
            try:
                DB_PATH.unlink(missing_ok=True)
            except Exception:
                pass
        with _connect() as conn:
            _create_schema(conn)
        return

    # Normal path (no repair, or file absent): ensure schema exists
    with _connect() as conn:
        _create_schema(conn)
