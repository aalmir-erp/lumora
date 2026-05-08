import os
import tempfile

import pytest


@pytest.fixture(autouse=True)
def isolated_db(monkeypatch):
    """Each test gets a fresh SQLite file, isolating settings/orders state."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    monkeypatch.setenv("DB_PATH", tmp.name)

    # Force re-import of modules that cache the path
    import importlib

    from app import db
    importlib.reload(db)
    db.init()
    yield
    os.unlink(tmp.name)
