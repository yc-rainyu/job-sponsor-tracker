import base64
import datetime
import json
import uuid

import jwt
import pytest
from sqlalchemy import func, select

from app.core.security import SESSION_COOKIE, create_session_token
from app.core.settings import settings
from app.models.user import AuthIdentity, User
from app.services import auth

CLAIMS = {
    'sub': '109876543210',
    'email': 'ada@example.com',
    'email_verified': True,
    'name': 'Ada Lovelace',
    'picture': 'https://example.com/ada.png',
}


@pytest.fixture
def fake_google(monkeypatch):
    def respond_with(claims):
        monkeypatch.setattr(
            auth.id_token, 'verify_oauth2_token', lambda *args, **kwargs: claims
        )

    respond_with(CLAIMS)
    return respond_with


def _token(secret, expires_in, user_id=None):
    expires = datetime.datetime.now(datetime.UTC) + expires_in
    return jwt.encode(
        {'sub': str(user_id or uuid.uuid4()), 'exp': expires}, secret, 'HS256'
    )


def _edit_payload(token):
    header, _payload, signature = token.split('.')
    payload = json.dumps({'sub': 'not-a-uuid', 'exp': 4102444800}).encode()
    edited = base64.urlsafe_b64encode(payload).rstrip(b'=').decode()
    return f'{header}.{edited}.{signature}'


def test_bad_google_token_is_rejected(client, monkeypatch):
    def reject(*args, **kwargs):
        raise ValueError('Token expired')

    monkeypatch.setattr(auth.id_token, 'verify_oauth2_token', reject)
    response = client.post('/auth/google', json={'credential': 'fake'})
    assert response.status_code == 401
    assert SESSION_COOKIE not in response.cookies


def test_unverified_email_is_rejected(client, fake_google):
    fake_google({**CLAIMS, 'email_verified': False})
    response = client.post('/auth/google', json={'credential': 'token'})
    assert response.status_code == 403


def test_sign_in_creates_user_and_sets_cookie(client, fake_google, session):
    response = client.post('/auth/google', json={'credential': 'token'})
    assert response.status_code == 200
    body = response.json()
    assert body['email'] == 'ada@example.com'
    assert body['display_name'] == 'Ada Lovelace'
    assert body['is_demo'] is False
    cookie = response.headers['set-cookie']
    for part in ['HttpOnly', 'Secure', 'SameSite=lax', 'Path=/', 'Max-Age=604800']:
        assert part in cookie
    assert session.scalar(select(func.count()).select_from(AuthIdentity)) == 1


def test_second_sign_in_reuses_user(client, fake_google, session):
    first = client.post('/auth/google', json={'credential': 'token'}).json()
    fake_google({**CLAIMS, 'name': 'Ada King'})
    second = client.post('/auth/google', json={'credential': 'token'}).json()
    assert second['id'] == first['id']
    assert second['display_name'] == 'Ada King'
    assert session.scalar(select(func.count()).select_from(User)) == 1


def test_me_after_sign_in(client, fake_google):
    user_id = client.post('/auth/google', json={'credential': 'token'}).json()['id']
    response = client.get('/auth/me')
    assert response.status_code == 200
    assert response.json()['id'] == user_id


def test_me_without_cookie(client):
    response = client.get('/auth/me')
    assert response.status_code == 401
    assert response.json() == {'detail': 'Not signed in. Sign in to continue.'}


@pytest.mark.parametrize(
    'token',
    [
        'not-a-jwt',
        _token('another-secret-that-is-32-chars-long', datetime.timedelta(days=1)),
        _edit_payload(create_session_token(uuid.uuid4())),
    ],
    ids=['not-a-jwt', 'wrong-key', 'edited-payload'],
)
def test_me_with_bad_cookie(client, token):
    client.cookies.set(SESSION_COOKIE, token)
    assert client.get('/auth/me').status_code == 401


def test_me_with_expired_cookie(client, session):
    user = User()
    session.add(user)
    session.flush()
    expired = _token(settings.jwt_secret, datetime.timedelta(seconds=-1), user.id)
    client.cookies.set(SESSION_COOKIE, expired)
    assert client.get('/auth/me').status_code == 401


def test_me_for_missing_user(client):
    client.cookies.set(SESSION_COOKIE, create_session_token(uuid.uuid4()))
    assert client.get('/auth/me').status_code == 401


def test_logout_then_me_is_401(client, fake_google):
    client.post('/auth/google', json={'credential': 'token'})
    assert client.get('/auth/me').status_code == 200
    response = client.post('/auth/logout')
    assert response.status_code == 204
    assert response.content == b''
    assert 'Max-Age=0' in response.headers['set-cookie']
    assert client.get('/auth/me').status_code == 401


def test_oversized_credential_is_rejected_before_google(client, monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError('should not reach Google verification')

    monkeypatch.setattr(auth.id_token, 'verify_oauth2_token', fail)
    response = client.post('/auth/google', json={'credential': 'x' * 4097})
    assert response.status_code == 422


def test_sign_in_attempts_are_limited_per_ip(client, fake_google, monkeypatch):
    monkeypatch.setattr(settings, 'google_rate_limit_per_minute', 2)
    for _ in range(2):
        assert (
            client.post('/auth/google', json={'credential': 'token'}).status_code == 200
        )
    response = client.post('/auth/google', json={'credential': 'token'})
    assert response.status_code == 429
    assert response.json() == {
        'detail': 'Too many sign-in attempts. Try again in a minute.'
    }
