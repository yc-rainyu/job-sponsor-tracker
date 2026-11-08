from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.core.rate_limit import limit_demo, limit_google
from app.core.security import (
    DEMO_SESSION_AGE,
    clear_session_cookie,
    create_session_token,
    set_session_cookie,
)
from app.models.user import User
from app.schemas.auth import DemoBody, GoogleSignInBody, Me
from app.services.auth import (
    delete_account,
    sign_in_google_user,
    verify_google_credential,
)
from app.services.demo import create_demo_user

router = APIRouter()


@router.post('/auth/google')
def google_sign_in(
    body: GoogleSignInBody,
    response: Response,
    session: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(limit_google)],
) -> Me:
    claims = verify_google_credential(body.credential)
    user = sign_in_google_user(session, claims)
    set_session_cookie(response, create_session_token(user.id))
    return Me.model_validate(user)


@router.post('/auth/demo')
def demo_sign_in(
    response: Response,
    session: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(limit_demo)],
    body: DemoBody | None = None,
) -> Me:
    user = create_demo_user(session, body.today if body else None)
    token = create_session_token(user.id, DEMO_SESSION_AGE)
    set_session_cookie(response, token, DEMO_SESSION_AGE)
    return Me.model_validate(user)


@router.get('/auth/me')
def me(user: Annotated[User, Depends(get_current_user)]) -> Me:
    return Me.model_validate(user)


# no valid session needed, so an expired cookie can still be cleared
@router.post('/auth/logout', status_code=204)
def logout(response: Response) -> None:
    clear_session_cookie(response)


@router.delete('/auth/account', status_code=204)
def delete_my_account(
    response: Response,
    session: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> None:
    delete_account(session, user)
    clear_session_cookie(response)
