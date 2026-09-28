import pytest
import os
from pathlib import Path
from backend.database.connection import init_db, SessionLocal, engine
from backend.database.models import Base
from backend.services.camera_manager import camera_manager

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Initializes the database and clears any residual state for testing."""
    init_db()
    yield
    camera_manager.shutdown_all()
