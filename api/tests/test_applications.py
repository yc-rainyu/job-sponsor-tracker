import csv
import io
import uuid

import pytest
from sqlalchemy import func, select

from app.core.security import SESSION_COOKIE, create_session_token
from app.models.application import Application
from app.models.user import User

MINIMAL = {
    'company': 'Roofoods Ltd t/a Deliveroo',
    'role': 'Backend engineer',
    'country': 'UK',
}
ON_LIST = {
    'status': 'on_list',
    'sponsor_id': 1,
    'registered_name': 'Roofoods Ltd t/a Deliveroo',
    'town': 'London',
    'match_type': 'trading_name',
    'score': 0.95,
    'has_skilled_worker': True,
    'rating': 'A',
    'checked_at': '2026-11-04T10:00:00Z',
    'register_published_on': '2026-10-16',
}
EMPTY_SKILLS = {'required': [], 'nice_to_have': []}
SKILLS = {
    'required': ['Python', 'PostgreSQL'],
    'nice_to_have': ['Docker'],
}
ANALYSIS = {
    'visa': 'declines',
    'salary': {
        'min': 50000,
        'max': 60000,
        'currency': 'GBP',
        'period': 'year',
        'raw': '£50,000 - £60,000 per annum',
    },
    'work_mode': 'hybrid',
    'experience_years': {'min': 3, 'max': None, 'raw': '3+ years'},
}


def _new_user(session):
    user = User()
    session.add(user)
    session.flush()
    return user


def _sign_in(client, user):
    client.cookies.set(SESSION_COOKIE, create_session_token(user.id))


def _create(client, **overrides):
    response = client.post('/applications', json={**MINIMAL, **overrides})
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture
def user(client, session):
    user = _new_user(session)
    _sign_in(client, user)
    return user


@pytest.fixture
def other_user(session):
    return _new_user(session)


def test_list_requires_sign_in(client):
    assert client.get('/applications').status_code == 401


def test_create_fills_defaults(client, user):
    body = _create(client)
    assert body['company'] == 'Roofoods Ltd t/a Deliveroo'
    assert body['status'] == 'applied'
    assert body['work_mode'] == 'unknown'
    assert body['channel'] == 'other'
    assert body['is_approx'] is False
    assert body['cover_letter'] == ''
    assert body['applied_on'] is None
    assert body['sponsor_check'] == {
        'status': 'unchecked',
        'sponsor_id': None,
        'registered_name': None,
        'town': None,
        'match_type': None,
        'score': None,
        'has_skilled_worker': None,
        'rating': None,
        'checked_at': None,
        'register_published_on': None,
    }
    assert body['skills'] == EMPTY_SKILLS
    assert body['analysis'] is None
    assert body['status_changed_at'] is not None
    assert body['created_at'] is not None


def test_create_keeps_skills_and_analysis(client, user):
    body = _create(client, skills=SKILLS, analysis=ANALYSIS, jd_text='We hire.')
    assert body['skills'] == SKILLS
    assert body['analysis'] == ANALYSIS
    assert body['jd_text'] == 'We hire.'


def test_create_trims_skill_names(client, user):
    body = _create(client, skills={'required': ['  Python  ']})
    assert body['skills'] == {
        'required': ['Python'],
        'nice_to_have': [],
    }


def test_create_keeps_sponsor_check(client, user):
    body = _create(client, sponsor_check=ON_LIST, applied_on='2026-11-01')
    assert body['sponsor_check']['status'] == 'on_list'
    assert body['sponsor_check']['registered_name'] == 'Roofoods Ltd t/a Deliveroo'
    assert body['sponsor_check']['register_published_on'] == '2026-10-16'
    assert body['applied_on'] == '2026-11-01'


@pytest.mark.parametrize(
    'bad',
    [
        {'company': None},
        {'company': '   '},
        {'status': 'hired'},
        {'country': 'FR'},
        {'sponsor_check': {'status': 'maybe'}},
        {'skills': {'required': ['x' * 101]}},
        {'skills': {'required': ['Python'] * 51}},
        {'skills': {'required': ['']}},
        {'skills': ['Python']},
        {'analysis': {'visa': 'maybe'}},
        {
            'analysis': {
                'visa': 'none',
                'salary': {'max': 1, 'currency': 'GBP', 'raw': 'x' * 201},
            }
        },
    ],
    ids=[
        'no-company',
        'blank-company',
        'bad-status',
        'bad-country',
        'bad-sponsor',
        'skill-too-long',
        'too-many-skills',
        'blank-skill',
        'skills-not-grouped',
        'bad-visa',
        'salary-raw-too-long',
    ],
)
def test_create_rejects_bad_values(client, user, bad):
    payload = {**MINIMAL, **bad}
    payload = {key: value for key, value in payload.items() if value is not None}
    assert client.post('/applications', json=payload).status_code == 422


def test_list_returns_only_own_records(client, user, other_user):
    _create(client, company='Mine One')
    _create(client, company='Mine Two')
    _sign_in(client, other_user)
    _create(client, company='Theirs')
    _sign_in(client, user)
    companies = [row['company'] for row in client.get('/applications').json()]
    assert sorted(companies) == ['Mine One', 'Mine Two']


def test_list_is_newest_first_with_undated_last(client, user):
    _create(client, company='Undated')
    _create(client, company='Older', applied_on='2026-10-01')
    _create(client, company='Newer', applied_on='2026-11-01')
    companies = [row['company'] for row in client.get('/applications').json()]
    assert companies == ['Newer', 'Older', 'Undated']


def test_get_own_record(client, user):
    created = _create(client)
    response = client.get(f'/applications/{created["id"]}')
    assert response.status_code == 200
    assert response.json() == created


def test_get_someone_elses_record_is_404(client, user, other_user):
    created = _create(client)
    _sign_in(client, other_user)
    response = client.get(f'/applications/{created["id"]}')
    assert response.status_code == 404
    assert response.json() == {'detail': 'Application not found.'}


def test_get_unknown_id_is_404(client, user):
    assert client.get(f'/applications/{uuid.uuid4()}').status_code == 404


def test_get_malformed_id_is_422(client, user):
    assert client.get('/applications/not-a-uuid').status_code == 422


def test_patch_status_updates_status_changed_at(client, user):
    created = _create(client)
    response = client.patch(
        f'/applications/{created["id"]}', json={'status': 'interviewing'}
    )
    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'interviewing'
    assert body['status_changed_at'] > created['status_changed_at']
    assert body['updated_at'] >= created['updated_at']


def test_patch_other_fields_keeps_status_changed_at(client, user):
    created = _create(client)
    body = client.patch(
        f'/applications/{created["id"]}',
        json={'notes': 'Recruiter called', 'status': 'applied'},
    ).json()
    assert body['notes'] == 'Recruiter called'
    assert body['status_changed_at'] == created['status_changed_at']


def test_patch_can_clear_optional_field(client, user):
    created = _create(client, applied_on='2026-11-01', next_step='Call back')
    body = client.patch(
        f'/applications/{created["id"]}', json={'applied_on': None, 'next_step': None}
    ).json()
    assert body['applied_on'] is None
    assert body['next_step'] is None


def test_patch_skills_and_clear_analysis(client, user):
    created = _create(client, skills=SKILLS, analysis=ANALYSIS)
    body = client.patch(
        f'/applications/{created["id"]}',
        json={'skills': {'required': ['Go']}, 'analysis': None},
    ).json()
    assert body['skills'] == {'required': ['Go'], 'nice_to_have': []}
    assert body['analysis'] is None


def test_patch_other_fields_keeps_skills(client, user):
    created = _create(client, skills=SKILLS)
    body = client.patch(f'/applications/{created["id"]}', json={'notes': 'x'}).json()
    assert body['skills'] == SKILLS


@pytest.mark.parametrize(
    'field', ['company', 'status', 'sponsor_check', 'is_approx', 'skills']
)
def test_patch_rejects_null_on_required_field(client, user, field):
    created = _create(client)
    response = client.patch(f'/applications/{created["id"]}', json={field: None})
    assert response.status_code == 422


def test_patch_someone_elses_record_is_404(client, user, other_user):
    created = _create(client)
    _sign_in(client, other_user)
    response = client.patch(f'/applications/{created["id"]}', json={'status': 'offer'})
    assert response.status_code == 404
    _sign_in(client, user)
    assert client.get(f'/applications/{created["id"]}').json()['status'] == 'applied'


def test_delete_own_record(client, user):
    created = _create(client)
    response = client.delete(f'/applications/{created["id"]}')
    assert response.status_code == 204
    assert response.content == b''
    assert client.get(f'/applications/{created["id"]}').status_code == 404


def test_delete_someone_elses_record_is_404_and_keeps_it(
    client, user, other_user, session
):
    created = _create(client)
    _sign_in(client, other_user)
    assert client.delete(f'/applications/{created["id"]}').status_code == 404
    assert session.scalar(select(func.count()).select_from(Application)) == 1


@pytest.fixture
def filter_set(client, user):
    _create(client, company='Deliveroo', country='UK', sponsor_check=ON_LIST)
    _create(
        client, company='Appier', country='TW', status='rejected', location='Taipei'
    )
    _create(client, company='Booking.com', country='NL', notes='Referred by a friend')


@pytest.mark.parametrize(
    ('params', 'expected'),
    [
        ({'country': 'TW'}, ['Appier']),
        ({'status': 'rejected'}, ['Appier']),
        ({'status': 'applied'}, ['Booking.com', 'Deliveroo']),
        ({'sponsor_status': 'on_list'}, ['Deliveroo']),
        ({'sponsor_status': 'unchecked'}, ['Appier', 'Booking.com']),
        ({'q': 'deliveroo'}, ['Deliveroo']),
        ({'q': 'taipei'}, ['Appier']),
        ({'q': 'friend'}, ['Booking.com']),
        ({'q': '%'}, []),
        ({'country': 'UK', 'status': 'rejected'}, []),
    ],
    ids=[
        'country',
        'status',
        'status-many',
        'sponsor-status',
        'sponsor-unchecked',
        'q-company',
        'q-location',
        'q-notes',
        'q-wildcard-is-literal',
        'combined',
    ],
)
def test_list_filters(client, filter_set, params, expected):
    rows = client.get('/applications', params=params).json()
    assert sorted(row['company'] for row in rows) == expected


def test_list_rejects_unknown_filter_value(client, user):
    assert client.get('/applications', params={'status': 'hired'}).status_code == 422


def test_export_csv(client, user, other_user):
    _create(client, company='Deliveroo', applied_on='2026-11-01', sponsor_check=ON_LIST)
    _sign_in(client, other_user)
    _create(client, company='Theirs')
    _sign_in(client, user)
    response = client.get('/applications/export.csv')
    assert response.status_code == 200
    assert response.headers['content-type'].startswith('text/csv')
    assert 'attachment' in response.headers['content-disposition']
    lines = response.text.splitlines()
    assert lines[0].startswith('applied_on,is_approx,country,company,role,')
    assert len(lines) == 2
    assert lines[1].startswith('2026-11-01,False,UK,Deliveroo,Backend engineer,')
    assert 'on_list,Roofoods Ltd t/a Deliveroo' in lines[1]
    assert 'Theirs' not in response.text


def test_export_csv_takes_the_list_filters(client, user):
    _create(client, company='Deliveroo', status='interviewing')
    _create(client, company='Monzo', status='applied')
    response = client.get('/applications/export.csv', params={'status': 'interviewing'})
    assert response.status_code == 200
    lines = response.text.splitlines()
    assert len(lines) == 2
    assert 'Deliveroo' in lines[1]
    assert 'Monzo' not in response.text


def test_export_csv_defuses_formulas(client, user):
    _create(
        client,
        company='=HYPERLINK("https://example.com","Click")',
        role='@SUM(A1:A9)',
        location='-',
        notes='+44 20 7946 0000',
    )
    response = client.get('/applications/export.csv')
    row = next(csv.DictReader(io.StringIO(response.text)))
    assert row['company'] == '\'=HYPERLINK("https://example.com","Click")'
    assert row['role'] == "'@SUM(A1:A9)"
    assert row['location'] == "'-"
    assert row['notes'] == "'+44 20 7946 0000"
    assert row['country'] == 'UK'


def test_export_csv_requires_sign_in(client):
    assert client.get('/applications/export.csv').status_code == 401
