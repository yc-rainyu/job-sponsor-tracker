from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.settings import settings
from app.models.register import RegisterSnapshot

router = APIRouter()


@router.get('/health')
def health(session: Annotated[Session, Depends(get_db)]) -> dict[str, str | None]:
    session.execute(text('SELECT 1'))
    published = session.scalar(
        select(RegisterSnapshot.published_date)
        .order_by(RegisterSnapshot.id.desc())
        .limit(1)
    )
    return {
        'status': 'ok',
        'db': 'ok',
        'version': settings.version,
        'register_published_on': published.isoformat() if published else None,
    }
