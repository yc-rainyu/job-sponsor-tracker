import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# 1. 先讀根目錄 .env，再改成連 jst_test（必須在 import app 之前）
_env_path = Path(__file__).resolve().parents[2] / '.env'
for _line in _env_path.read_text().splitlines():
    _line = _line.strip()
    if not _line or _line.startswith('#') or '=' not in _line:
        continue
    _key, _value = _line.split('=', 1)
    os.environ.setdefault(_key, _value)

_url = os.environ['DATABASE_URL']
os.environ['DATABASE_URL'] = _url.rsplit('/', 1)[0] + '/jst_test'
os.environ['APP_ENV'] = 'test'

# 2. 現在才 import（此時 settings / engine 會連 jst_test）
from app.db.engine import engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_connection():
    with engine.connect() as conn:
        with conn.begin() as trans:
            yield conn
            trans.rollback()
