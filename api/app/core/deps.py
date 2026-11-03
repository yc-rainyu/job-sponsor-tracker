from collections.abc import Generator
from typing import Annotated

import jwt
from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import SESSION_COOKIE, read_session_token
from app.db.engine import SessionLocal
from app.models.user import User


def get_db() -> Generator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


_NOT_SIGNED_IN = 'Not signed in. Sign in to continue.'


def get_current_user(
    session: Annotated[Session, Depends(get_db)],
    token: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> User:
    if token is None:
        raise HTTPException(status_code=401, detail=_NOT_SIGNED_IN)
    try:
        user_id = read_session_token(token)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail=_NOT_SIGNED_IN) from None
    # the account may have been deleted after the cookie was issued
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail=_NOT_SIGNED_IN)
    return user
