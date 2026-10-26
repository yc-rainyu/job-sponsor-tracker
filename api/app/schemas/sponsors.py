import datetime
from typing import Literal

from pydantic import BaseModel


class SponsorHit(BaseModel):
    id: int
    registered_name: str
    trading_name: str | None
    town: str | None
    rating: Literal['A', 'B'] | None
    routes: list[str]
    has_skilled_worker: bool
    match_type: Literal['exact', 'alias', 'trading_name', 'word', 'fuzzy']
    score: float


class SearchResult(BaseModel):
    hits: list[SponsorHit]
    total: int


class RegisterInfo(BaseModel):
    published_on: datetime.date | None
