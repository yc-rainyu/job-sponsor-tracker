from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.rate_limit import limit_search
from app.services.sponsors.search import search_sponsors

router = APIRouter()

@router.get('/sponsors/search')
def search(
    session: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(limit_search)],
    q: str = '',
    limit: int = 10,
):
    return [hit._asdict() for hit in search_sponsors(session, q, limit)]