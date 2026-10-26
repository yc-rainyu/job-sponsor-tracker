from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.rate_limit import limit_analyse
from app.services.jd_rules import analyse
from app.services.sponsors.search import search_sponsors

router = APIRouter()


class AnalyseBody(BaseModel):
    text: str = Field(max_length=20000)
    company: str | None = Field(default=None, max_length=200)


@router.post('/jd/analyse')
def analyse_jd(
    body: AnalyseBody,
    session: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(limit_analyse)],
):
    result = analyse(body.text)
    company = (body.company or '').strip()
    if company:
        hits, _ = search_sponsors(session, company)
        result['company_matches'] = [hit._asdict() for hit in hits]
    else:
        result['company_matches'] = []
    return result
