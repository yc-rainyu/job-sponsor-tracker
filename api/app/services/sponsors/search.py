from typing import NamedTuple

from sqlalchemy import case, false, func, or_, select
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models.register import Sponsor, SponsorAlias, SponsorRoute
from app.services.sponsors.normalise import normalise_name

_LEGAL_SUFFIXES = {'ltd', 'plc', 'llp', 'co'}


class SearchHit(NamedTuple):
    id: int
    registered_name: str
    trading_name: str | None
    town: str | None
    rating: str | None
    routes: list[str]
    has_skilled_worker: bool
    match_type: str
    score: float


def search_sponsors(
    session: Session, query: str, limit: int = 10, offset: int = 0
) -> tuple[list[SearchHit], int]:
    query_norm, _, _ = normalise_name(query)
    # blank, or only suffixes that most of the register shares
    if set(query_norm.split()) <= _LEGAL_SUFFIXES:
        return [], 0

    # looked up first, as a subquery it stops the trigram indexes being used
    alias_ids = set(
        session.scalars(
            select(SponsorAlias.sponsor_id).where(SponsorAlias.alias_norm == query_norm)
        )
    )

    exact = or_(
        Sponsor.legal_name_norm == query_norm,
        Sponsor.trading_name_norm == query_norm,
    )
    alias = Sponsor.id.in_(alias_ids) if alias_ids else false()
    trading_sim = func.word_similarity(query_norm, Sponsor.trading_name_norm)
    word_sim = func.word_similarity(query_norm, Sponsor.legal_name_norm)
    fuzzy_sim = func.similarity(query_norm, Sponsor.legal_name_norm)
    trading_hit = trading_sim >= settings.search_trading_threshold
    word_hit = word_sim >= settings.search_word_threshold
    fuzzy_hit = fuzzy_sim >= settings.search_fuzzy_threshold

    match_type = case(
        (exact, 'exact'),
        (alias, 'alias'),
        (trading_hit, 'trading_name'),
        (word_hit, 'word'),
        else_='fuzzy',
    ).label('match_type')
    score = case(
        (exact, 1.0),
        (alias, 0.98),
        (trading_hit, trading_sim),
        (word_hit, word_sim),
        else_=fuzzy_sim,
    ).label('score')

    matches = session.execute(
        select(
            Sponsor.id,
            Sponsor.name_raw,
            Sponsor.trading_name_raw,
            Sponsor.town,
            match_type,
            score,
            func.count().over().label('total'),
        )
        .where(
            Sponsor.removed_time.is_(None),
            # operators narrow rows through the GIN indexes using pg_trgm's own
            # thresholds (0.6, 0.3), the next filter applies the settings
            or_(
                exact,
                alias,
                Sponsor.trading_name_norm.op('%>')(query_norm),
                Sponsor.legal_name_norm.op('%>')(query_norm),
                Sponsor.legal_name_norm.op('%')(query_norm),
            ),
            or_(exact, alias, trading_hit, word_hit, fuzzy_hit),
        )
        .order_by(score.desc(), func.coalesce(Sponsor.town, ''), Sponsor.id)
        .limit(limit)
        .offset(offset)
    ).all()
    if not matches:
        return [], 0

    ids = [match.id for match in matches]
    route_rows = session.scalars(
        select(SponsorRoute)
        .where(SponsorRoute.sponsor_id.in_(ids))
        .order_by(SponsorRoute.route)
    ).all()
    routes_by_id = {}
    ratings_by_id = {}
    for row in route_rows:
        routes_by_id.setdefault(row.sponsor_id, []).append(row.route)
        ratings_by_id.setdefault(row.sponsor_id, []).append(row.type_rating)

    hits = []
    for match in matches:
        routes = routes_by_id.get(match.id, [])
        hits.append(
            SearchHit(
                id=match.id,
                registered_name=match.name_raw,
                trading_name=match.trading_name_raw,
                town=match.town,
                rating=_rating(ratings_by_id.get(match.id, [])),
                routes=routes,
                has_skilled_worker='Skilled Worker' in routes,
                match_type=match.match_type,
                score=match.score,
            )
        )
    return hits, matches[0].total


def _rating(type_ratings: list[str]) -> str | None:
    if any('B rating' in raw for raw in type_ratings):
        return 'B'
    # A (Premium) and A (SME+) are A ratings too
    if any('(A ' in raw for raw in type_ratings):
        return 'A'
    return None
