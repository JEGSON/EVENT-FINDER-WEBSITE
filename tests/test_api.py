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

