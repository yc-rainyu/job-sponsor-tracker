import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Prefer env already set (CI); otherwise load root .env for local runs.
_env_path = Path(__file__).resolve().parents[2] / '.env'
if 'DATABASE_URL' not in os.environ and _env_path.is_file():
    for _line in _env_path.read_text().splitlines():
        _line = _line.strip()
        if not _line or _line.startswith('#') or '=' not in _line:
            continue
        _key, _value = _line.split('=', 1)
        os.environ.setdefault(_key, _value)

_url = os.environ['DATABASE_URL']
os.environ['DATABASE_URL'] = _url.rsplit('/', 1)[0] + '/jst_test'
os.environ['APP_ENV'] = 'test'

from app.db.engine import engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def session():
    with engine.connect() as conn:
        trans = conn.begin()
        sess = Session(conn)
        yield sess
        sess.close()
        trans.rollback()
