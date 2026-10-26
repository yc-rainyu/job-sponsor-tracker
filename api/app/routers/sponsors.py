from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.rate_limit import limit_search
from app.services.sponsors.search import search_sponsors

router = APIRouter()


@router.get('/sponsors/search')
def search(
    session: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(limit_search)],
    query: Annotated[str, Query(alias='q')] = '',
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    hits, total = search_sponsors(session, query, limit, offset)
    return {'hits': [hit._asdict() for hit in hits], 'total': total}
