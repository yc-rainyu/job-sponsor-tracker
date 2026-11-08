import datetime
import uuid

from sqlalchemy import func, select, update

from app.core.settings import settings
from app.models.application import Application
from app.models.user import User
from app.services.demo import load_seed


def _two_days_ago():
    return datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=2)


def test_seed_file_is_valid():
    rows = load_seed()
    assert len(rows) == 30
    for row in rows:
        if row.sponsor_check.status == 'on_list':
            assert row.sponsor_check.registered_name and row.sponsor_check.town
        else:
            assert row.sponsor_check.registered_name is None


def test_demo_signs_in_a_throwaway_user(client):
    response = client.post('/auth/demo')
    assert response.status_code == 200
    body = response.json()
    assert body['is_demo'] is True
    assert body['email'] is None
    assert body['display_name'] == 'Demo user'
    cookie = response.headers['set-cookie']
    for part in ['HttpOnly', 'Secure', 'SameSite=lax', 'Path=/', 'Max-Age=86400']:
        assert part in cookie
    assert client.get('/auth/me').json()['id'] == body['id']


def test_demo_user_gets_the_seed_applications(client):
    client.post('/auth/demo')
    rows = client.get('/applications').json()
    assert len(rows) == 30
    today = datetime.datetime.now(datetime.UTC).date().isoformat()
    assert rows[0]['applied_on'] == today
    assert rows[-1]['applied_on'] is None
    assert {row['sponsor_check']['status'] for row in rows} == {
        'on_list',
        'not_found',
        'agency',
        'not_applicable',
        'unchecked',
    }
    assert rows[0]['status_changed_at'].startswith(today)


def test_demo_looks_up_sponsor_ids_in_the_register(client, seed_sponsors):
    seed_sponsors()
    client.post('/auth/demo')
    checks = {
        row['company']: row['sponsor_check']
        for row in client.get('/applications').json()
    }
    deliveroo = checks['Deliveroo']
    assert deliveroo['sponsor_id'] is not None
    assert deliveroo['checked_at'] is not None
    assert deliveroo['register_published_on'] == '2026-10-16'

    assert checks['Monzo']['sponsor_id'] is None
    assert checks['Monzo']['checked_at'] is not None
    assert checks['Capital One']['checked_at'] is None
    assert checks['Booking.com']['register_published_on'] is None


def test_each_demo_is_a_new_user(client):
    first = client.post('/auth/demo').json()['id']
    second = client.post('/auth/demo').json()['id']
    assert first != second


def test_expired_demo_users_are_removed_with_their_applications(client, session):
    expired = uuid.UUID(client.post('/auth/demo').json()['id'])
    recent = uuid.UUID(client.post('/auth/demo').json()['id'])
    session.execute(
        update(User).where(User.id == expired).values(created_at=_two_days_ago())
    )
    regular = User(email='old@example.com', created_at=_two_days_ago())
    session.add(regular)
    session.flush()

    fresh = uuid.UUID(client.post('/auth/demo').json()['id'])

    ids = set(session.scalars(select(User.id)))
    assert expired not in ids
    assert {recent, regular.id, fresh} <= ids
    owners = set(session.scalars(select(Application.user_id).distinct()))
    assert owners == {recent, fresh}
    assert session.scalar(select(func.count()).select_from(Application)) == 60


def test_demo_rate_limit(client, monkeypatch):
    monkeypatch.setattr(settings, 'demo_rate_limit_per_hour', 2)
    assert client.post('/auth/demo').status_code == 200
    assert client.post('/auth/demo').status_code == 200
    response = client.post('/auth/demo')
    assert response.status_code == 429
    assert 'hour' in response.json()['detail']


def test_demo_uses_the_browsers_date(client):
    tomorrow = datetime.datetime.now(datetime.UTC).date() + datetime.timedelta(days=1)
    client.post('/auth/demo', json={'today': tomorrow.isoformat()})
    rows = client.get('/applications').json()
    assert rows[0]['applied_on'] == tomorrow.isoformat()


def test_demo_ignores_dates_far_from_utc(client):
    client.post('/auth/demo', json={'today': '2000-01-01'})
    rows = client.get('/applications').json()
    assert (
        rows[0]['applied_on'] == datetime.datetime.now(datetime.UTC).date().isoformat()
    )
