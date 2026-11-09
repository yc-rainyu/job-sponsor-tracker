import datetime
from collections.abc import Mapping
from typing import Any

from fastapi import HTTPException
from google.auth.transport import requests
from google.oauth2 import id_token
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models.user import AuthIdentity, User


def verify_google_credential(credential: str) -> Mapping[str, Any]:
    try:
        claims = id_token.verify_oauth2_token(
            credential,
            requests.Request(),
            settings.google_client_id,
            # small clock differences would reject a token that was just issued
            clock_skew_in_seconds=10,
        )
    except ValueError:
        # every bad token raises ValueError
        raise HTTPException(
            status_code=401, detail='Google sign-in failed. Try signing in again.'
        ) from None
    if not claims.get('email_verified'):
        raise HTTPException(
            status_code=403,
            detail='Your Google email is not verified. Verify it, then sign in again.',
        )
    return claims


def sign_in_google_user(session: Session, claims: Mapping[str, Any]) -> User:
    user = session.scalar(
        select(User)
        .join(AuthIdentity)
        .where(
            AuthIdentity.provider == 'google',
            AuthIdentity.provider_subject == claims['sub'],
        )
    )
    if user is None:
        user = User()
        session.add(user)
        session.flush()
        session.add(
            AuthIdentity(
                user_id=user.id, provider='google', provider_subject=claims['sub']
            )
        )
    user.email = claims['email']
    user.display_name = claims.get('name')
    user.avatar_url = claims.get('picture')
    user.last_login_at = datetime.datetime.now(datetime.UTC)
    session.commit()
    return user


def delete_account(session: Session, user: User) -> None:
    # applications, auth_identities and ai_usage go with it through ON DELETE CASCADE
    session.delete(user)
    session.commit()
