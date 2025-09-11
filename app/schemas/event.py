"""Pydantic models and enums for Events domain.

These schemas define request/response models and search parameters, and provide
validators to normalize and sanitize common fields.
"""

from datetime import date
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class CategoryEnum(str, Enum):
    """Supported event categories."""
    music = "music"
    tech = "tech"
    sports = "sports"
    arts = "arts"
    business = "business"
    community = "community"


class EventBase(BaseModel):
    """Shared fields for events.

    All text inputs are stripped, and ``category`` is normalized to lowercase
    and validated against :class:`CategoryEnum`.
    """
    title: str = Field(..., max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    location: str = Field(..., max_length=200)
    category: CategoryEnum
    date: date

    @field_validator("title", "location", "description", mode="before")
    @classmethod
    def _strip_text(cls, v):
        """Trim whitespace from textual fields if provided."""
        if v is None:
            return v
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("category", mode="before")
    @classmethod
    def _normalize_category(cls, v):
        """Normalize category strings to lower-case enum values."""
        if v is None:
            return v
        if isinstance(v, str):
            return CategoryEnum(v.strip().lower())
        return v


class EventCreate(EventBase):
    """Payload for creating a new event."""


class EventOut(EventBase):
    """Event payload returned by the API."""
    id: int
    created_at: str

    class Config:
        from_attributes = True


class SortEnum(str, Enum):
    """Supported sorting modes for event listing."""
    date_asc = "date_asc"
    date_desc = "date_desc"
    created_desc = "created_desc"


class EventQuery(BaseModel):
    """Search and pagination options for listing events."""
    q: Optional[str] = None
    location: Optional[str] = None
    date: Optional[date] = None # type: ignore
    category: Optional[CategoryEnum] = None
    start_date: Optional[date] = None # type: ignore
    end_date: Optional[date] = None # type: ignore
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)
    sort: SortEnum = SortEnum.date_asc


class EventUpdate(BaseModel):
    """Partial update payload for events."""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    location: Optional[str] = Field(None, max_length=200)
    category: Optional[CategoryEnum] = None
    date: Optional[date] = None # type: ignore

    @field_validator("title", "location", "description", mode="before")
    @classmethod
    def _strip_text(cls, v):
        """Trim whitespace from textual fields if provided."""
        if v is None:
            return v
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("category", mode="before")
    @classmethod
    def _normalize_category(cls, v):
        """Normalize category strings to lower-case enum values."""
        if v is None:
            return v
        if isinstance(v, str):
            return CategoryEnum(v.strip().lower())
        return v
