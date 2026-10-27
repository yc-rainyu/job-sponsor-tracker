from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.settings import settings
from app.schemas.health import Health

router = APIRouter()


# uptime monitors send HEAD and FastAPI does not answer it on GET routes
@router.get('/health')
@router.head('/health', include_in_schema=False)
def health(session: Annotated[Session, Depends(get_db)]) -> Health:
    session.execute(text('SELECT 1'))
    return Health(status='ok', db='ok', version=settings.version)
