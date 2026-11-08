import uuid

import pytest
from sqlalchemy import func, select

from app.core.security import SESSION_COOKIE, create_session_token
from app.models.application import Application
from app.models.user import AuthIdentity, User
from app.services import auth

CLAIMS = {'sub': '109876543210', 'email': 'ada@example.com', 'email_verified': True}
APPLICATION = {'company': 'Acme Ltd', 'role': 'Backend engineer', 'country': 'UK'}


@pytest.fixture
def sign_in(client, monkeypatch):
    monkeypatch.setattr(
        auth.id_token, 'verify_oauth2_token', lambda *args, **kwargs: CLAIMS
    )

    def sign_in():
        response = client.post('/auth/google', json={'credential': 'token'})
        assert response.status_code == 200
        return uuid.UUID(response.json()['id'])

    return sign_in


def _count(session, model, user_id):
    return session.scalar(
        select(func.count()).select_from(model).where(model.user_id == user_id)
    )


def test_delete_account_removes_user_and_their_data(client, session, sign_in):
    other = User()
    session.add(other)
    session.flush()
    client.cookies.set(SESSION_COOKIE, create_session_token(other.id))
    assert client.post('/applications', json=APPLICATION).status_code == 201

    user_id = sign_in()
    for _ in range(2):
        assert client.post('/applications', json=APPLICATION).status_code == 201

    response = client.delete('/auth/account')
    assert response.status_code == 204
    assert 'Max-Age=0' in response.headers['set-cookie']
    assert session.get(User, user_id) is None
    assert _count(session, AuthIdentity, user_id) == 0
    assert _count(session, Application, user_id) == 0
    assert _count(session, Application, other.id) == 1


def test_old_cookie_stops_working(client, sign_in):
    sign_in()
    token = client.cookies.get(SESSION_COOKIE)
    client.delete('/auth/account')
    assert client.get('/auth/me').status_code == 401
    client.cookies.set(SESSION_COOKIE, token)
    assert client.get('/auth/me').status_code == 401


def test_signing_in_again_starts_an_empty_account(client, sign_in):
    first_id = sign_in()
    client.post('/applications', json=APPLICATION)
    client.delete('/auth/account')
    assert sign_in() != first_id
    assert client.get('/applications').json() == []


def test_delete_account_needs_sign_in(client):
    assert client.delete('/auth/account').status_code == 401
