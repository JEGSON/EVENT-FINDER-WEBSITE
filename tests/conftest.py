import importlib
import os
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    # Create a temporary SQLite file for the test session
    return tmp_path_factory.mktemp("data") / "test.db"


@pytest.fixture(scope="session")
def app(test_db_path: Path):
    # Point the app at the test DB before importing modules that read the env
    os.environ["EVENTFINDER_DATABASE_PATH"] = str(test_db_path)

    # Reload config and database so they pick up the env var
    from app.core import config as cfg
    from app.core import database as db
    importlib.reload(cfg)
    importlib.reload(db)

    # Now import and construct the FastAPI app
    from app import main as main_module
    importlib.reload(main_module)
    return main_module.create_app()

