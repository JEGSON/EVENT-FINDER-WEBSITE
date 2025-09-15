from __future__ import annotations

"""Data access layer for events.

Contains thin, well-typed helpers that translate between SQLite rows and
Pydantic models and construct SQL for filtering, sorting, and pagination.
"""

from typing import Any, Dict, Iterable, List, Optional
import re
import sqlite3

from ..schemas.event import EventCreate, EventOut, EventQuery, EventUpdate, SortEnum


def _fts_available(conn: sqlite3.Connection) -> bool:
    cur = conn.cursor()
    try:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events_fts'")
        return cur.fetchone() is not None
    except sqlite3.Error:
        return False


def _to_fts_query(text: str) -> str:
    """Convert free text into a simple FTS5 query.

    Splits on non-word characters and applies prefix search with AND between
    tokens, e.g., "lagos tech" -> "lagos* AND tech*".
    """
    tokens = re.findall(r"\w+", text.lower())
    if not tokens:
        return ""
    return " AND ".join(f"{t}*" for t in tokens)


def row_to_event(row: sqlite3.Row) -> EventOut:
    """Convert a SQLite Row into an EventOut model."""
    return EventOut(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        location=row["location"],
        category=row["category"],
        date=row["date"],
        created_at=row["created_at"],
    )


def insert_event(conn: sqlite3.Connection, data: EventCreate) -> EventOut:
    """Insert a new event and return the persisted record."""
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO events (title, description, location, category, date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (data.title, data.description, data.location, data.category.value, data.date.isoformat()),
        )
        event_id = cur.lastrowid
        conn.commit()  # Add commit here
        cur.execute("SELECT * FROM events WHERE id = ?", (event_id,))
        row = cur.fetchone()
        return row_to_event(row)
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()


def list_events(conn: sqlite3.Connection, q: EventQuery) -> List[EventOut]:
    """List events matching search criteria with pagination and sorting."""
    joins: List[str] = []
    clauses: List[str] = []
    params: List[Any] = []

    if q.q:
        if _fts_available(conn):
            joins.append("JOIN events_fts fts ON fts.rowid = events.id")
            clauses.append("fts MATCH ?")
            params.append(_to_fts_query(q.q))
        else:
            clauses.append("(title LIKE ? OR description LIKE ?)")
            like = f"%{q.q}%"
            params.extend([like, like])
    if getattr(q, 'starts_with', None):
        clauses.append("LOWER(title) LIKE ?")
        params.append(f"{q.starts_with.lower()}%") # type: ignore
    if q.location:
        clauses.append("LOWER(location) LIKE ?")
        params.append(f"%{q.location.lower()}%")
    if q.category:
        clauses.append("LOWER(category) = ?")
        params.append(q.category.value)
    if q.date:
        clauses.append("date = ?")
        params.append(q.date.isoformat())
    if q.start_date:
        clauses.append("date >= ?")
        params.append(q.start_date.isoformat())
    if q.end_date:
        clauses.append("date <= ?")
        params.append(q.end_date.isoformat())

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    join_sql = " ".join(joins)
    # Sorting
    if q.sort == SortEnum.date_desc:
        order = "ORDER BY date DESC, id DESC"
    elif q.sort == SortEnum.created_desc:
        order = "ORDER BY created_at DESC, id DESC"
    else:
        order = "ORDER BY date ASC, id ASC"
    sql = f"SELECT events.* FROM events {join_sql} {where} {order} LIMIT ? OFFSET ?"
    params.extend([q.limit, q.offset])

    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    return [row_to_event(r) for r in rows]


def count_events(conn: sqlite3.Connection, q: EventQuery) -> int:
    """Count total events matching the given filters (ignores limit/offset)."""
    joins: List[str] = []
    clauses: List[str] = []
    params: List[Any] = []

    if q.q:
        if _fts_available(conn):
            joins.append("JOIN events_fts fts ON fts.rowid = events.id")
            clauses.append("fts MATCH ?")
            params.append(_to_fts_query(q.q))
        else:
            clauses.append("(title LIKE ? OR description LIKE ?)")
            like = f"%{q.q}%"
            params.extend([like, like])
    if getattr(q, 'starts_with', None):
        clauses.append("LOWER(title) LIKE ?")
        params.append(f"{q.starts_with.lower()}%") # type: ignore
    if q.location:
        clauses.append("LOWER(location) LIKE ?")
        params.append(f"%{q.location.lower()}%")
    if q.category:
        clauses.append("LOWER(category) = ?")
        params.append(q.category.value)
    if q.date:
        clauses.append("date = ?")
        params.append(q.date.isoformat())
    if q.start_date:
        clauses.append("date >= ?")
        params.append(q.start_date.isoformat())
    if q.end_date:
        clauses.append("date <= ?")
        params.append(q.end_date.isoformat())

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    join_sql = " ".join(joins)
    sql = f"SELECT COUNT(*) AS cnt FROM events {join_sql} {where}"
    cur = conn.cursor()
    cur.execute(sql, params)
    row = cur.fetchone()
    return int(row[0]) if row else 0


def get_event(conn: sqlite3.Connection, event_id: int) -> Optional[EventOut]:
    """Fetch a single event by ID, or None if not found."""
    cur = conn.cursor()
    cur.execute("SELECT * FROM events WHERE id = ?", (event_id,))
    row = cur.fetchone()
    return row_to_event(row) if row else None


def update_event(conn: sqlite3.Connection, event_id: int, updates: EventUpdate) -> Optional[EventOut]:
    """Apply partial updates and return the updated event or None if not found."""
    data = updates.model_dump(exclude_unset=True)
    if not data:
        return get_event(conn, event_id)
    
    fields = []
    params: List[Any] = []
    if "title" in data:
        fields.append("title = ?")
        params.append(data["title"])
    if "description" in data:
        fields.append("description = ?")
        params.append(data["description"])
    if "location" in data:
        fields.append("location = ?")
        params.append(data["location"])
    if "category" in data:
        fields.append("category = ?")
        params.append(data["category"].value if hasattr(data["category"], 'value') else data["category"])  # type: ignore
    if "date" in data:
        fields.append("date = ?")
        params.append(data["date"].isoformat())

    if not fields:
        return get_event(conn, event_id)

    params.append(event_id)
    sql = f"UPDATE events SET {', '.join(fields)} WHERE id = ?"
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        conn.commit()  # Add commit here
        if cur.rowcount == 0:
            return None
        cur.execute("SELECT * FROM events WHERE id = ?", (event_id,))
        row = cur.fetchone()
        return row_to_event(row) if row else None
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()


def delete_event(conn: sqlite3.Connection, event_id: int) -> bool:
    """Delete an event by ID. Returns True if a row was removed."""
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM events WHERE id = ?", (event_id,))
        conn.commit()  # Add commit here - this was the main issue!
        return cur.rowcount > 0
    except Exception as e:
        conn.rollback()  # Rollback on error
        raise e
    finally:
        cur.close()  # Clean up cursor