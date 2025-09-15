"""Application entrypoint and FastAPI app factory.

This module wires middleware, routers, and startup hooks.
Use ``uvicorn app.main:app --reload --port 8001`` to run the API locally.
"""

import logging
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
import sqlite3
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .core.database import init_db
from .api.routes import events as events_router
from .api.routes import meta as meta_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: A configured FastAPI instance with CORS, routes, and startup.
    """
    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Total-Count"],
    )

    @app.on_event("startup")
    def _startup() -> None:
        """Initialize local SQLite database and indexes on startup."""
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
        init_db()
        logging.getLogger(__name__).info("DB initialized and ready")

    @app.get("/health")
    def health() -> dict:
        """Simple liveness endpoint used by monitors and tests."""
        return {"status": "ok"}

    @app.get("/ready")
    def ready(conn: sqlite3.Connection = Depends(get_db)) -> dict:
        """Readiness probe that verifies the app can talk to SQLite.

        Returns 200 with status ok when a trivial DB query succeeds; 503 otherwise.
        Suitable for container orchestrator health checks (e.g., Render).
        """
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1")
            _ = cur.fetchone()
            return {"status": "ok", "db": "ok"}
        except Exception:
            # Avoid leaking internals in readiness path
            raise HTTPException(status_code=503, detail="unready")

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        """Redirect the API root to the interactive Swagger docs."""
        return RedirectResponse(url="/docs", status_code=307)

    app.include_router(events_router.router, prefix="/api")
    app.include_router(meta_router.router, prefix="/api")
    return app


app = create_app()
