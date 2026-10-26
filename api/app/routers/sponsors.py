from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.rate_limit import limit_search
from app.models.register import RegisterSnapshot
from app.schemas.sponsors import RegisterInfo, SearchResult
from app.services.sponsors.search import search_sponsors

router = APIRouter()


@router.get('/sponsors/search')
def search(
    session: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(limit_search)],
    query: Annotated[str, Query(alias='q', max_length=200)] = '',
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> SearchResult:
    hits, total = search_sponsors(session, query, limit, offset)
    return SearchResult(hits=hits, total=total)


@router.get('/sponsors/register')
def register_info(session: Annotated[Session, Depends(get_db)]) -> RegisterInfo:
    published_on = session.scalar(
        select(RegisterSnapshot.published_date)
        .order_by(RegisterSnapshot.id.desc())
        .limit(1)
    )
    return RegisterInfo(published_on=published_on)
