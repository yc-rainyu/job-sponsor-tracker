from typing import Annotated, Literal

from fastapi import APIRouter, Cookie, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.core.rate_limit import limit_analyse
from app.core.security import SESSION_COOKIE
from app.schemas.jd import AnalyseBody, AnalyseResult
from app.services.jd_ai import analyse_with_ai
from app.services.jd_rules import analyse
from app.services.sponsors.search import search_sponsors

router = APIRouter()


@router.post('/jd/analyse')
def analyse_jd(
    body: AnalyseBody,
    session: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(limit_analyse)],
    mode: Literal['rules', 'ai'] = 'rules',
    token: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> AnalyseResult:
    if mode == 'ai':
        user = get_current_user(session, token)
        result = analyse_with_ai(session, user, body.text)
    else:
        result = analyse(body.text)
    hits, _total = search_sponsors(session, body.company or '')
    return AnalyseResult(**result, company_matches=hits)
