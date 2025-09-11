"""Miscellaneous metadata endpoints (e.g., category list)."""

from fastapi import APIRouter

from ...schemas.event import CategoryEnum


router = APIRouter(prefix="/meta", tags=["meta"])


@router.get("/categories", response_model=list[str])
def list_categories() -> list[str]:
    """Return all supported event categories as strings."""
    return [c.value for c in CategoryEnum]
