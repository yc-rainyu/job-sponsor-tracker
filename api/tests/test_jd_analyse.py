from pathlib import Path

from app.core.settings import settings
from tests.test_sponsor_search import _seed

FIXTURES = Path(__file__).parent / 'fixtures' / 'jd'


def _analyse(client, text, company=None):
    body = {'text': text}
    if company is not None:
        body['company'] = company
    return client.post('/jd/analyse', json=body)


def test_declines(client):
    text = (FIXTURES / '01-declines-explicit.txt').read_text()
    response = _analyse(client, text)
    assert response.status_code == 200
    body = response.json()
    assert body['visa']['verdict'] == 'declines'
    assert body['company_matches'] == []


def test_too_long(client):
    response = _analyse(client, 'x' * 20001)
    assert response.status_code == 422


def test_company_match(client, session, tmp_path):
    _seed(session, tmp_path)
    text = (FIXTURES / '01-declines-explicit.txt').read_text()
    response = _analyse(client, text, company='Deliveroo')
    assert response.status_code == 200
    names = [row['registered_name'] for row in response.json()['company_matches']]
    assert names == ['Roofoods Ltd t/a Deliveroo']


def test_rate_limit(client, monkeypatch):
    monkeypatch.setattr(settings, 'analyse_rate_limit_per_minute', 2)
    text = 'Python required.'
    assert _analyse(client, text).status_code == 200
    assert _analyse(client, text).status_code == 200
    response = _analyse(client, text)
    assert response.status_code == 429
    assert response.json()['detail']
