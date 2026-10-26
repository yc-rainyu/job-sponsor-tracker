from typing import NamedTuple

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models.register import Sponsor, SponsorAlias, SponsorRoute
from app.services.sponsors.normalise import normalise_name


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
    if not query_norm:
        return [], 0

    alias_ids = set(
        session.scalars(
            select(SponsorAlias.sponsor_id).where(SponsorAlias.alias_norm == query_norm)
        )
    )

    trading_sim = func.word_similarity(query_norm, Sponsor.trading_name_norm)
    word_sim = func.word_similarity(query_norm, Sponsor.legal_name_norm)
    fuzzy_sim = func.similarity(query_norm, Sponsor.legal_name_norm)

    rows = session.execute(
        select(Sponsor, trading_sim, word_sim, fuzzy_sim).where(
            Sponsor.removed_time.is_(None),
            or_(
                Sponsor.legal_name_norm == query_norm,
                Sponsor.trading_name_norm == query_norm,
                Sponsor.id.in_(alias_ids) if alias_ids else False,
                Sponsor.trading_name_norm.op('%>')(query_norm),
                Sponsor.legal_name_norm.op('%>')(query_norm),
                Sponsor.legal_name_norm.op('%')(query_norm),
            ),
        )
    ).all()

    ranked = []
    for sponsor, trading_sim, word_sim, fuzzy_sim in rows:
        match_type, score = _pick_layer(
            sponsor, query_norm, alias_ids, trading_sim, word_sim, fuzzy_sim
        )
        if match_type is None:
            continue
        ranked.append((sponsor, match_type, score))

    ranked.sort(key=lambda item: (-item[2], item[0].town or ''))
    total = len(ranked)
    ranked = ranked[offset : offset + limit]

    ids = [sponsor.id for sponsor, _, _ in ranked]
    if not ids:
        return [], total
    route_rows = session.scalars(
        select(SponsorRoute).where(SponsorRoute.sponsor_id.in_(ids))
    ).all()
    routes_by_id = {}
    ratings_by_id = {}
    for row in route_rows:
        routes_by_id.setdefault(row.sponsor_id, []).append(row.route)
        ratings_by_id.setdefault(row.sponsor_id, []).append(row.type_rating)

    hits = []
    for sponsor, match_type, score in ranked:
        routes = routes_by_id.get(sponsor.id, [])
        hits.append(
            SearchHit(
                id=sponsor.id,
                registered_name=sponsor.name_raw,
                trading_name=sponsor.trading_name_raw,
                town=sponsor.town,
                rating=_rating(ratings_by_id.get(sponsor.id, [])),
                routes=routes,
                has_skilled_worker='Skilled Worker' in routes,
                match_type=match_type,
                score=score,
            )
        )
    return hits, total


def _pick_layer(sponsor, query_norm, alias_ids, trading_sim, word_sim, fuzzy_sim):
    if sponsor.legal_name_norm == query_norm or sponsor.trading_name_norm == query_norm:
        return 'exact', 1.0
    if sponsor.id in alias_ids:
        return 'alias', 0.98
    if trading_sim is not None and trading_sim >= settings.search_trading_threshold:
        return 'trading_name', float(trading_sim)
    if word_sim is not None and word_sim >= settings.search_word_threshold:
        return 'word', float(word_sim)
    if fuzzy_sim is not None and fuzzy_sim >= settings.search_fuzzy_threshold:
        return 'fuzzy', float(fuzzy_sim)
    return None, 0.0


def _rating(type_ratings):
    for raw in type_ratings:
        if 'B rating' in raw:
            return 'B'
        if 'A rating' in raw:
            return 'A'
    return None
