import time
from collections import defaultdict

from fastapi import HTTPException, Request

from app.core.settings import settings

_hits: dict[str, list[float]] = defaultdict(list)
_WINDOW = 60.0


def reset() -> None:
    _hits.clear()


def limit_search(request: Request) -> None:
    ip = request.client.host if request.client else 'unknown'
    now = time.monotonic()
    recent = [t for t in _hits[ip] if now - t < _WINDOW]
    if len(recent) >= settings.search_rate_limit_per_minute:
        raise HTTPException(
            status_code=429,
            detail='Too many searches. Try again in a minute.',
        )
    recent.append(now)
    _hits[ip] = recent