import secrets
import threading
import time
from typing import Annotated

from fastapi import Depends, HTTPException, Request

from app.core.deps import get_current_user
from app.core.settings import settings
from app.models.user import User

MINUTE = 60.0
HOUR = 3600.0
_MAX_KEYS = 10_000
_hits: dict[str, list[float]] = {}
# sync dependencies run in a thread pool, so two requests can check at once
_lock = threading.Lock()


def reset() -> None:
    with _lock:
        _hits.clear()


def client_ip(request: Request) -> str:
    """The visitor's IP: the one Next's proxy vouches for, else the connection's."""
    connection_ip = request.client.host if request.client else 'unknown'
    # an unset key would match an empty header, so unset means the feature is off
    if not settings.proxy_key:
        return connection_ip
    forwarded = request.headers.get('X-Jst-Client-Ip')
    sent_key = request.headers.get('X-Jst-Proxy-Key', '')
    # bytes, because compare_digest raises on non-ascii str and anyone can send one
    if forwarded and secrets.compare_digest(
        sent_key.encode(), settings.proxy_key.encode()
    ):
        return forwarded
    return connection_ip


def _limit(key: str, max_hits: int, window: float, detail: str) -> None:
    now = time.monotonic()
    with _lock:
        recent = [stamp for stamp in _hits.get(key, []) if now - stamp < window]
        if len(recent) >= max_hits:
            raise HTTPException(status_code=429, detail=detail)
        recent.append(now)
        _hits[key] = recent

        if len(_hits) > _MAX_KEYS:
            quiet = [old for old, stamps in _hits.items() if now - stamps[-1] >= HOUR]
            for old in quiet:
                del _hits[old]


def limit_search(request: Request) -> None:
    _limit(
        f'search:{client_ip(request)}',
        settings.search_rate_limit_per_minute,
        MINUTE,
        'Too many searches. Try again in a minute.',
    )


def limit_analyse(request: Request) -> None:
    _limit(
        f'analyse:{client_ip(request)}',
        settings.analyse_rate_limit_per_minute,
        MINUTE,
        'Too many analyses. Try again in a minute.',
    )


def limit_demo(request: Request) -> None:
    _limit(
        f'demo:{client_ip(request)}',
        settings.demo_rate_limit_per_hour,
        HOUR,
        'Too many demo accounts from this network. Try again in an hour.',
    )


def limit_google(request: Request) -> None:
    _limit(
        f'google:{client_ip(request)}',
        settings.google_rate_limit_per_minute,
        MINUTE,
        'Too many sign-in attempts. Try again in a minute.',
    )


# keyed by account, so switching networks does not reset the count
def limit_writes(user: Annotated[User, Depends(get_current_user)]) -> None:
    _limit(
        f'writes:{user.id}',
        settings.write_rate_limit_per_minute,
        MINUTE,
        'Too many changes. Try again in a minute.',
    )
