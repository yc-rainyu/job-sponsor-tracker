from app.core.settings import settings


def _search(client, query, **params):
    return client.get('/sponsors/search', params={'q': query, **params})


def _hits(response):
    return response.json()['hits']


def _names(response):
    return [row['registered_name'] for row in _hits(response)]


# exact match on the trading name
def test_deliveroo(client, seed_sponsors):
    seed_sponsors()
    response = _search(client, 'Deliveroo')
    assert response.status_code == 200
    rows = _hits(response)
    assert _names(response) == ['Roofoods Ltd t/a Deliveroo']
    row = rows[0]
    assert row['trading_name'] == 'Deliveroo'
    assert row['town'] == 'London'
    assert row['rating'] == 'A'
    assert row['has_skilled_worker'] is True
    assert 'Skilled Worker' in row['routes']
    assert row['match_type'] == 'exact'
    assert row['score'] == 1.0


# missing letter on the trading name
def test_delivero(client, seed_sponsors):
    seed_sponsors()
    response = _search(client, 'Delivero')
    assert response.status_code == 200
    rows = _hits(response)
    assert _names(response) == ['Roofoods Ltd t/a Deliveroo']
    assert rows[0]['match_type'] == 'trading_name'


# brand name from the alias list
def test_admiral(client, seed_sponsors):
    seed_sponsors()
    response = _search(client, 'Admiral')
    assert response.status_code == 200
    rows = _hits(response)
    assert _names(response) == ['Eui Limited']
    assert rows[0]['town'] == 'Cardiff'
    assert rows[0]['match_type'] == 'alias'
    assert rows[0]['score'] == 0.98


def test_exxonmobil(client, seed_sponsors):
    seed_sponsors()
    response = _search(client, 'ExxonMobil')
    assert response.status_code == 200
    rows = _hits(response)
    assert _names(response) == ['ESSO Petroleum Company Ltd']
    assert rows[0]['town'] == 'Leatherhead'
    assert rows[0]['match_type'] == 'alias'


# every J.P. Morgan we seeded
def test_jp_morgan(client, seed_sponsors):
    seed_sponsors()
    response = _search(client, 'JP Morgan')
    assert response.status_code == 200
    assert set(_names(response)) == {
        'J.P. Morgan Chase Bank N.A.',
        'J.P. Morgan Europe Limited',
        'J.P. Morgan Securities plc',
    }


# legal name is longer than the query
def test_stripe(client, seed_sponsors):
    seed_sponsors()
    response = _search(client, 'Stripe')
    assert response.status_code == 200
    rows = _hits(response)
    assert 'Stripe Payments UK Ltd' in _names(response)
    assert rows[0]['match_type'] != 'exact'


# unknown name is empty
def test_unknown(client, seed_sponsors):
    seed_sponsors()
    response = _search(client, 'Definitely Not A Sponsor')
    assert response.status_code == 200
    assert _hits(response) == []
    assert response.json()['total'] == 0


# blank query is empty
def test_blank(client, seed_sponsors):
    seed_sponsors()
    response = _search(client, '')
    assert response.status_code == 200
    assert _hits(response) == []
    assert response.json()['total'] == 0


def test_offset(client, seed_sponsors):
    seed_sponsors()
    first = _search(client, 'JP Morgan', limit=1, offset=0)
    second = _search(client, 'JP Morgan', limit=1, offset=1)
    assert first.json()['total'] == 3
    assert second.json()['total'] == 3
    assert _hits(first)[0]['id'] != _hits(second)[0]['id']


# no hits past the last page, but total still counts every match
def test_offset_past_end(client, seed_sponsors):
    seed_sponsors()
    response = _search(client, 'JP Morgan', offset=10)
    assert _hits(response) == []
    assert response.json()['total'] == 3


# B on any route wins over A
def test_mixed_rating(client, seed_sponsors):
    seed_sponsors()
    response = _search(client, 'Mixed Licence')
    assert _names(response) == ['Mixed Licence Ltd']
    assert _hits(response)[0]['rating'] == 'B'


# Premium is still an A rating
def test_premium_rating(client, seed_sponsors):
    seed_sponsors()
    response = _search(client, 'Premium Rated')
    assert _names(response) == ['Premium Rated Ltd']
    assert _hits(response)[0]['rating'] == 'A'


# a bare legal suffix would match most of the register
def test_suffix_only(client, seed_sponsors):
    seed_sponsors()
    response = _search(client, 'Ltd')
    assert response.status_code == 200
    assert _hits(response) == []
    assert response.json()['total'] == 0


# the suffix alone used to make most of the register match
def test_suffix_ignored_for_fuzzy(client, seed_sponsors):
    seed_sponsors()
    response = _search(client, 'A Ltd')
    assert response.json()['total'] == 0


def test_exact_before_word_tie(client, seed_sponsors):
    seed_sponsors()
    rows = _hits(_search(client, 'Roofoods Ltd'))
    assert [row['registered_name'] for row in rows[:2]] == [
        'Roofoods Ltd t/a Deliveroo',
        'Roofoods Holdings Ltd',
    ]
    assert rows[0]['match_type'] == 'exact'
    assert rows[1]['score'] == 1.0


# the other name scores 1.0 on "admiral", the alias still goes first
def test_alias_before_word_match(client, seed_sponsors):
    seed_sponsors(['Admiral Care Ltd,Leeds,,Worker (A rating),Skilled Worker'])
    response = _search(client, 'Admiral')
    assert _names(response) == ['Eui Limited', 'Admiral Care Ltd']


def test_query_too_long(client):
    response = _search(client, 'a' * 201)
    assert response.status_code == 422


# third call in the same minute is rejected
def test_rate_limit(client, seed_sponsors, monkeypatch):
    seed_sponsors()
    monkeypatch.setattr(settings, 'search_rate_limit_per_minute', 2)

    assert _search(client, 'Deliveroo').status_code == 200
    assert _search(client, 'Deliveroo').status_code == 200
    response = _search(client, 'Deliveroo')
    assert response.status_code == 429
    assert response.json()['detail']


# the footer reads the date of the latest import
def test_register_date(client, seed_sponsors):
    seed_sponsors()
    response = client.get('/sponsors/register')
    assert response.status_code == 200
    assert response.json() == {'published_on': '2026-10-16'}
