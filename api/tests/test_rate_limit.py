import pytest

from app.core.settings import settings

KEY = 'test-proxy-key'
IP_A = {'X-Jst-Client-Ip': '203.0.113.1'}
IP_B = {'X-Jst-Client-Ip': '203.0.113.2'}


def _analyse(client, headers):
    return client.post(
        '/jd/analyse', json={'text': 'Python required.'}, headers=headers
    )


@pytest.fixture
def one_per_minute(monkeypatch):
    monkeypatch.setattr(settings, 'analyse_rate_limit_per_minute', 1)
    monkeypatch.setattr(settings, 'proxy_key', KEY)


def test_right_key_counts_per_forwarded_ip(client, one_per_minute):
    vouched = {'X-Jst-Proxy-Key': KEY}
    assert _analyse(client, vouched | IP_A).status_code == 200
    assert _analyse(client, vouched | IP_B).status_code == 200
    assert _analyse(client, vouched | IP_A).status_code == 429


@pytest.mark.parametrize(
    'headers',
    [{'X-Jst-Proxy-Key': 'wrong'}, {}, {'X-Jst-Proxy-Key': ''}],
    ids=['wrong key', 'no key', 'empty key'],
)
def test_other_keys_fall_back_to_connection_ip(client, one_per_minute, headers):
    assert _analyse(client, headers | IP_A).status_code == 200
    assert _analyse(client, headers | IP_B).status_code == 429


def test_right_key_without_ip_falls_back(client, one_per_minute):
    assert _analyse(client, {}).status_code == 200
    assert _analyse(client, {'X-Jst-Proxy-Key': KEY}).status_code == 429


def test_non_ascii_key_falls_back_instead_of_500(client, one_per_minute):
    headers = {b'X-Jst-Proxy-Key': b'cl\xe9', **IP_A}
    assert _analyse(client, headers).status_code == 200
    assert _analyse(client, {b'X-Jst-Proxy-Key': b'cl\xe9', **IP_B}).status_code == 429


def test_unset_key_ignores_headers(client, monkeypatch):
    monkeypatch.setattr(settings, 'analyse_rate_limit_per_minute', 1)
    monkeypatch.setattr(settings, 'proxy_key', '')
    empty = {'X-Jst-Proxy-Key': ''}
    assert _analyse(client, empty | IP_A).status_code == 200
    assert _analyse(client, empty | IP_B).status_code == 429
