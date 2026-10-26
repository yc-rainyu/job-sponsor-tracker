import time
from collections import defaultdict

from fastapi import HTTPException, Request

from app.core.settings import settings

_hits: dict[str, list[float]] = defaultdict(list)
_WINDOW = 60.0


def reset() -> None:
    _hits.clear()


def _limit(request: Request, name: str, max_hits: int, detail: str) -> None:
    ip = request.client.host if request.client else 'unknown'
    key = f'{name}:{ip}'
    now = time.monotonic()
    recent = [stamp for stamp in _hits[key] if now - stamp < _WINDOW]
    if len(recent) >= max_hits:
        raise HTTPException(status_code=429, detail=detail)
    recent.append(now)
    _hits[key] = recent


def limit_search(request: Request) -> None:
    _limit(
        request,
        'search',
        settings.search_rate_limit_per_minute,
        'Too many searches. Try again in a minute.',
    )


def limit_analyse(request: Request) -> None:
    _limit(
        request,
        'analyse',
        settings.analyse_rate_limit_per_minute,
        'Too many analyses. Try again in a minute.',
    )
