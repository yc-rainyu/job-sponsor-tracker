from datetime import date

from app.models.register import RegisterSnapshot


def test_health_ok(client):
    response = client.get('/health')
    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'ok'
    assert body['db'] == 'ok'
    assert body['version']
    assert 'register_published_on' in body


def test_health_register_date(client, session):
    session.add(
        RegisterSnapshot(
            published_date=date(2026, 10, 16),
            source_file='register.csv',
            row_count=1,
            org_count=1,
            added_count=1,
            removed_count=0,
        )
    )
    session.flush()
    body = client.get('/health').json()
    assert body['register_published_on'] == '2026-10-16'
