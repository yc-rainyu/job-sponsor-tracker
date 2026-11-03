from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.core.security import (
    clear_session_cookie,
    create_session_token,
    set_session_cookie,
)
from app.models.user import User
from app.schemas.auth import GoogleSignInBody, Me
from app.services.auth import sign_in_google_user, verify_google_credential

router = APIRouter()


@router.post('/auth/google')
def google_sign_in(
    body: GoogleSignInBody,
    response: Response,
    session: Annotated[Session, Depends(get_db)],
) -> Me:
    claims = verify_google_credential(body.credential)
    user = sign_in_google_user(session, claims)
    set_session_cookie(response, create_session_token(user.id))
    return Me.model_validate(user)


@router.get('/auth/me')
def me(user: Annotated[User, Depends(get_current_user)]) -> Me:
    return Me.model_validate(user)


# no valid session needed, so an expired cookie can still be cleared
@router.post('/auth/logout', status_code=204)
def logout(response: Response) -> None:
    clear_session_cookie(response)
