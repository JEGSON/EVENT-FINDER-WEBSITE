from datetime import date

import pytest
import httpx
from fastapi import FastAPI


@pytest.mark.asyncio
async def test_health(app: FastAPI):
    transport = httpx.ASGITransport(app=app, lifespan="on")
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_categories(app: FastAPI):
    transport = httpx.ASGITransport(app=app, lifespan="on")
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/meta/categories")
        assert r.status_code == 200
        cats = r.json()
        assert isinstance(cats, list) and "music" in cats


@pytest.mark.asyncio
async def test_create_get_and_list_event(app: FastAPI):
    transport = httpx.ASGITransport(app=app, lifespan="on")
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "title": "PyCon Meetup",
            "description": "A great Python event",
            "location": "Online",
            "category": "tech",
            "date": date.today().isoformat(),
        }

        # Create
        r = await client.post("/api/events/", json=payload)
        assert r.status_code == 201
        created = r.json()
        assert created["id"] > 0
        assert created["title"] == payload["title"]

        # Get by id
        r = await client.get(f"/api/events/{created['id']}")
        assert r.status_code == 200
        fetched = r.json()
        assert fetched["id"] == created["id"]

        # List/search
        r = await client.get("/api/events/?limit=10&offset=0")
        assert r.status_code == 200
        assert "X-Total-Count" in r.headers
        items = r.json()
        assert any(evt["id"] == created["id"] for evt in items)


@pytest.mark.asyncio
async def test_update_event_partial(app: FastAPI):
    transport = httpx.ASGITransport(app=app, lifespan="on")
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Seed an event
        payload = {
            "title": "Original Title",
            "description": "desc",
            "location": "Lagos",
            "category": "tech",
            "date": date.today().isoformat(),
        }
        r = await client.post("/api/events/", json=payload)
        assert r.status_code == 201
        evt = r.json()

        # Partial update: title trim + category normalization
        patch = {"title": "  Updated Title  ", "category": "MUSIC"}
        r = await client.patch(f"/api/events/{evt['id']}", json=patch)
        assert r.status_code == 200
        updated = r.json()
        assert updated["title"] == "Updated Title"
        assert updated["category"] == "music"

        # Fetch again to ensure persisted
        r = await client.get(f"/api/events/{evt['id']}")
        assert r.status_code == 200
        fetched = r.json()
        assert fetched["title"] == "Updated Title"
        assert fetched["category"] == "music"


@pytest.mark.asyncio
async def test_delete_event_and_404_after(app: FastAPI):
    transport = httpx.ASGITransport(app=app, lifespan="on")
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "title": "To Delete",
            "description": None,
            "location": "Remote",
            "category": "community",
            "date": date.today().isoformat(),
        }
        r = await client.post("/api/events/", json=payload)
        assert r.status_code == 201
        evt = r.json()

        # Delete the event
        r = await client.delete(f"/api/events/{evt['id']}")
        assert r.status_code == 204

        # Subsequent GET should be 404
        r = await client.get(f"/api/events/{evt['id']}")
        assert r.status_code == 404


@pytest.mark.asyncio
async def test_update_delete_nonexistent_return_404(app: FastAPI):
    transport = httpx.ASGITransport(app=app, lifespan="on")
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.patch("/api/events/999999", json={"title": "Nope"})
        assert r.status_code == 404
        r = await client.delete("/api/events/999999")
        assert r.status_code == 404
