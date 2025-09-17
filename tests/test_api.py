from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with app.router.lifespan_context(app):
        yield


@pytest_asyncio.fixture
async def client(app: FastAPI):
    async with lifespan(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as async_client:
            yield async_client


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_categories(client: AsyncClient) -> None:
    response = await client.get("/api/meta/categories")
    assert response.status_code == 200
    categories = response.json()
    assert isinstance(categories, list) and "music" in categories


@pytest.mark.asyncio
async def test_create_get_and_list_event(client: AsyncClient) -> None:
    payload = {
        "title": "PyCon Meetup",
        "description": "A great Python event",
        "location": "Online",
        "category": "tech",
        "date": date.today().isoformat(),
    }

    create_response = await client.post("/api/events/", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["id"] > 0
    assert created["title"] == payload["title"]

    detail_response = await client.get(f"/api/events/{created['id']}")
    assert detail_response.status_code == 200
    fetched = detail_response.json()
    assert fetched["id"] == created["id"]

    list_response = await client.get("/api/events/?limit=10&offset=0")
    assert list_response.status_code == 200
    assert "X-Total-Count" in list_response.headers
    items = list_response.json()
    assert any(evt["id"] == created["id"] for evt in items)


@pytest.mark.asyncio
async def test_update_event_partial(client: AsyncClient) -> None:
    payload = {
        "title": "Original Title",
        "description": "desc",
        "location": "Lagos",
        "category": "tech",
        "date": date.today().isoformat(),
    }
    create_response = await client.post("/api/events/", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()

    patch = {"title": "  Updated Title  ", "category": "MUSIC"}
    update_response = await client.patch(f"/api/events/{created['id']}", json=patch)
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["title"] == "Updated Title"
    assert updated["category"] == "music"

    detail_response = await client.get(f"/api/events/{created['id']}")
    assert detail_response.status_code == 200
    fetched = detail_response.json()
    assert fetched["title"] == "Updated Title"
    assert fetched["category"] == "music"


@pytest.mark.asyncio
async def test_delete_event_and_404_after(client: AsyncClient) -> None:
    payload = {
        "title": "To Delete",
        "description": None,
        "location": "Remote",
        "category": "community",
        "date": date.today().isoformat(),
    }
    create_response = await client.post("/api/events/", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()

    delete_response = await client.delete(f"/api/events/{created['id']}")
    assert delete_response.status_code == 204

    detail_response = await client.get(f"/api/events/{created['id']}")
    assert detail_response.status_code == 404


@pytest.mark.asyncio
async def test_update_delete_nonexistent_return_404(client: AsyncClient) -> None:
    patch_response = await client.patch("/api/events/999999", json={"title": "Nope"})
    assert patch_response.status_code == 404

    delete_response = await client.delete("/api/events/999999")
    assert delete_response.status_code == 404
