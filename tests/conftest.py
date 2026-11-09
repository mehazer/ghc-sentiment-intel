import os
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

# Configure the database before `ghc` is imported anywhere.
_DB_PATH = Path(tempfile.gettempdir()) / "ghc_test.db"
os.environ["GHC_DATABASE_URL"] = f"sqlite:///{_DB_PATH}"


@pytest.fixture(scope="session")
def app_client():
    from fastapi.testclient import TestClient

    from ghc.db import Base, engine, init_db
    from ghc.main import app

    init_db()
    with TestClient(app) as client:
        yield client
    Base.metadata.drop_all(bind=engine)
    _DB_PATH.unlink(missing_ok=True)


@pytest.fixture()
def client(app_client):
    """Fresh tables per test: the app and module objects stay identical."""
    from ghc.db import Base, engine

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield app_client
