from fastapi import APIRouter
from sqlalchemy import text

from app.core.settings import settings
from app.db.engine import engine

router = APIRouter()


@router.get('/health')
def health() -> dict[str, str]:
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    return {'status': 'ok', 'db': 'ok', 'version': settings.version}
