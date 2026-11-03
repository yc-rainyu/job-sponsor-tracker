import datetime
import uuid

import jwt
from fastapi import Response

from app.core.settings import settings

SESSION_COOKIE = 'session'
SESSION_AGE = datetime.timedelta(days=7)
_ALGORITHM = 'HS256'


def create_session_token(user_id: uuid.UUID) -> str:
    expires = datetime.datetime.now(datetime.UTC) + SESSION_AGE
    return jwt.encode(
        {
            'sub': str(user_id),
            'exp': expires,
        },
        settings.jwt_secret,
        algorithm=_ALGORITHM,
    )


def read_session_token(token: str) -> uuid.UUID:
    payload = jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[_ALGORITHM],
        options={'require': ['exp', 'sub']},
    )
    return uuid.UUID(payload['sub'])


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=int(SESSION_AGE.total_seconds()),
        path='/',
        secure=True,
        httponly=True,
        samesite='lax',
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        SESSION_COOKIE, path='/', secure=True, httponly=True, samesite='lax'
    )
