"""Events API routes.

This router exposes CRUD and search endpoints for events. Query parameters
support keyword search, location and category filters, date range filtering,
sorting, pagination, and a total-count response header.
"""

from datetime import date as _date
import sqlite3
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from ...core.database import get_db
from ...repositories.events import (
    count_events,
    delete_event,
    get_event,
    insert_event,
    list_events,
    update_event,
)
from ...schemas.event import (
    CategoryEnum,
    EventCreate,
    EventOut,
    EventQuery,
    EventUpdate,
    SortEnum,
)


def _parse_iso_date(value: Optional[str]) -> Optional[_date]:
    if value is None:
        return None
    return _date.fromisoformat(value)


router = APIRouter(prefix="/events", tags=["events"])


@router.post("/", response_model=EventOut, status_code=201)
def create_event(payload: EventCreate, conn: sqlite3.Connection = Depends(get_db)) -> EventOut:
    """Create a new event.

    Args:
        payload: Validated event payload.
        conn: Database connection (injected).

    Returns:
        The newly created event.
    """
    return insert_event(conn, payload)


@router.get("/", response_model=List[EventOut])
def search_events(
    response: Response,
    q: Optional[str] = Query(None, description="Keyword in title/description"),
    starts_with: Optional[str] = Query(None, pattern=r"^[A-Za-z]$", description="Filter by first letter of title"),
    location: Optional[str] = None,
    date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    category: Optional[CategoryEnum] = None,
    start_date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort: SortEnum = SortEnum.date_asc,
    conn: sqlite3.Connection = Depends(get_db),
) -> List[EventOut]:
    """Search and paginate events.

    Sets ``X-Total-Count`` header to the total number of matches.
    """
    parsed = EventQuery(
        q=q,
        starts_with=starts_with,
        location=location,
        date=_parse_iso_date(date),
        category=category,
        start_date=_parse_iso_date(start_date),
        end_date=_parse_iso_date(end_date),
        limit=limit,
        offset=offset,
        sort=sort,
    )
    total = count_events(conn, parsed)
    if response is not None:
        response.headers["X-Total-Count"] = str(total)
    return list_events(conn, parsed)


@router.get("/{event_id}", response_model=EventOut)
def get_event_by_id(event_id: int, conn: sqlite3.Connection = Depends(get_db)) -> EventOut:
    """Get a single event by ID.

    Raises 404 if the event is not found.
    """
    evt = get_event(conn, event_id)
    if not evt:
        raise HTTPException(status_code=404, detail="Event not found")
    return evt


@router.patch("/{event_id}", response_model=EventOut)
def patch_event(event_id: int, payload: EventUpdate, conn: sqlite3.Connection = Depends(get_db)) -> EventOut:
    """Partially update an event.

    Only provided fields are updated. Raises 404 if not found.
    """
    updated = update_event(conn, event_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Event not found")
    return updated


@router.delete("/{event_id}", status_code=204)
def delete_event_by_id(event_id: int, conn: sqlite3.Connection = Depends(get_db)) -> None:
    """Delete an event by ID.

    Returns 204 on success; raises 404 if not found.
    """
    ok = delete_event(conn, event_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Event not found")
