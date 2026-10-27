import threading
import time

from fastapi import HTTPException, Request

from app.core.settings import settings

_WINDOW = 60.0
_MAX_KEYS = 10_000
_hits: dict[str, list[float]] = {}
# sync dependencies run in a thread pool, so two requests can check at once
_lock = threading.Lock()


def reset() -> None:
    with _lock:
        _hits.clear()


def _limit(request: Request, name: str, max_hits: int, detail: str) -> None:
    ip = request.client.host if request.client else 'unknown'
    key = f'{name}:{ip}'
    now = time.monotonic()
    with _lock:
        recent = [stamp for stamp in _hits.get(key, []) if now - stamp < _WINDOW]
        if len(recent) >= max_hits:
            raise HTTPException(status_code=429, detail=detail)
        recent.append(now)
        _hits[key] = recent
        # forget ips that went quiet so memory does not keep growing
        if len(_hits) > _MAX_KEYS:
            quiet = [
                old for old, stamps in _hits.items() if now - stamps[-1] >= _WINDOW
            ]
            for old in quiet:
                del _hits[old]


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
