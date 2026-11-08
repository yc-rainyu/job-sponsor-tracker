import pytest

from app.core.security import SESSION_COOKIE, create_session_token
from app.core.settings import settings
from app.models.user import User

APPLICATION = {'company': 'Acme Ltd', 'role': 'Backend engineer', 'country': 'UK'}


def _sign_in_new_user(client, session, **fields):
    user = User(**fields)
    session.add(user)
    session.flush()
    client.cookies.set(SESSION_COOKIE, create_session_token(user.id))
    return user


def _create(client, **overrides):
    return client.post('/applications', json={**APPLICATION, **overrides})


def test_creates_and_updates_share_a_per_user_limit(client, session, monkeypatch):
    monkeypatch.setattr(settings, 'write_rate_limit_per_minute', 2)
    _sign_in_new_user(client, session)
    created = _create(client).json()
    assert (
        client.patch(f'/applications/{created["id"]}', json={'notes': 'x'}).status_code
        == 200
    )
    response = _create(client)
    assert response.status_code == 429
    assert response.json() == {'detail': 'Too many changes. Try again in a minute.'}
    assert client.get('/applications').status_code == 200

    # same IP, different account: its own allowance
    _sign_in_new_user(client, session)
    assert _create(client).status_code == 201


def test_application_limit(client, session, monkeypatch):
    monkeypatch.setattr(settings, 'application_limit', 2)
    _sign_in_new_user(client, session)
    first = _create(client).json()
    assert _create(client).status_code == 201
    response = _create(client)
    assert response.status_code == 429
    assert response.json() == {
        'detail': 'This account can hold up to 2 applications. Delete some to add more.'
    }
    client.delete(f'/applications/{first["id"]}')
    assert _create(client).status_code == 201


def test_demo_users_have_their_own_limit(client, session, monkeypatch):
    monkeypatch.setattr(settings, 'application_limit', 5)
    monkeypatch.setattr(settings, 'demo_application_limit', 1)
    _sign_in_new_user(client, session, is_demo=True)
    assert _create(client).status_code == 201
    assert _create(client).status_code == 429


SPONSOR_CHECK = {'status': 'on_list', 'sponsor_id': 1, 'score': 0.95}


@pytest.mark.parametrize(
    'field',
    [
        {'registered_name': 'x' * 501},
        {'town': 'x' * 201},
        {'score': 1.01},
        {'score': -0.1},
        {'sponsor_id': 0},
    ],
    ids=['long name', 'long town', 'score above 1', 'negative score', 'id 0'],
)
def test_sponsor_check_is_bounded(client, session, field):
    _sign_in_new_user(client, session)
    response = _create(client, sponsor_check={**SPONSOR_CHECK, **field})
    assert response.status_code == 422


def test_sponsor_check_accepts_the_bounds(client, session):
    _sign_in_new_user(client, session)
    check = {
        **SPONSOR_CHECK,
        'registered_name': 'x' * 500,
        'town': 'x' * 200,
        'score': 1.0,
    }
    assert _create(client, sponsor_check=check).status_code == 201
    assert _create(client, sponsor_check={**check, 'score': 0}).status_code == 201
