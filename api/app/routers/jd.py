from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.rate_limit import limit_analyse
from app.schemas.jd import AnalyseBody, AnalyseResult
from app.services.jd_rules import analyse
from app.services.sponsors.search import search_sponsors

router = APIRouter()


@router.post('/jd/analyse')
def analyse_jd(
    body: AnalyseBody,
    session: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(limit_analyse)],
) -> AnalyseResult:
    hits, _total = search_sponsors(session, body.company or '')
    return AnalyseResult(**analyse(body.text), company_matches=hits)
