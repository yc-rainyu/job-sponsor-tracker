import datetime
import json
import re

import pytest
from sqlalchemy import func, select

from app.models.application import Application
from app.models.user import User
from app.services.import_applications import (
    RowError,
    import_applications,
    map_row,
    sponsor_name,
)

EMAIL = 'import-test@example.com'
# one made-up row in the old tracker's export shape
OLD = {
    'id': 'acme-backend',
    'approx': False,
    'channel': '官網',
    'company': 'Acme Limited',
    'country': '英國',
    'coverLetter': '',
    'createdAt': '2026-10-13T08:50:10.000Z',
    'date': '2026-10-13',
    'location': 'London',
    'notes': 'Applied via the careers page',
    'role': 'Backend engineer',
    'salary': '',
    'status': '已送出',
    'updatedAt': '2026-10-20T02:50:00.000Z',
}
UTC = datetime.UTC


def _export(tmp_path, rows):
    path = tmp_path / 'export.json'
    path.write_text(json.dumps(rows, ensure_ascii=False))
    return path


def _count(session, user):
    return session.scalar(
        select(func.count())
        .select_from(Application)
        .where(Application.user_id == user.id)
    )


@pytest.fixture
def importer(session):
    user = User(email=EMAIL)
    session.add(user)
    session.flush()
    return user


def test_map_row_direct_fields():
    body = map_row(OLD, 0)
    assert body.company == 'Acme Limited'
    assert body.role == 'Backend engineer'
    assert body.country == 'UK'
    assert body.applied_on == datetime.date(2026, 10, 13)
    assert body.is_approx is False
    assert body.location == 'London'
    assert body.channel == 'company_site'
    assert body.status == 'applied'
    assert body.salary_stated is None
    assert body.cover_letter == ''
    assert body.notes == 'Applied via the careers page'
    assert body.sponsor_check.status == 'unchecked'
    assert body.sponsor_check.registered_name is None


@pytest.mark.parametrize(
    ('field', 'old', 'new'),
    [
        ('country', '台灣', 'TW'),
        ('country', '荷蘭', 'NL'),
        ('country', '美國（遠端）', 'US'),
        ('channel', '104', 'job_board_104'),
        ('channel', 'Cake', 'job_board_cake'),
        ('channel', '官網（從 LinkedIn 連過去）', 'company_site'),
        ('channel', '官網（LinkedIn 外）', 'company_site'),
        ('channel', 'LinkedIn 一鍵應徵', 'linkedin_easy_apply'),
        ('channel', 'Email', 'email'),
        ('channel', '', 'other'),
        ('channel', '主管主動邀約', 'other'),
        ('status', '面試中', 'interviewing'),
        ('status', '已拒絕', 'rejected'),
        ('status', '待確認送出', 'draft'),
    ],
)
def test_map_row_translates_values(field, old, new):
    assert getattr(map_row({**OLD, field: old}, 0), field) == new


@pytest.mark.parametrize(
    ('old', 'new'),
    [('', ''), ('無', ''), ('有', '有'), ('有（提到 OSINT）', '有（提到 OSINT）')],
    ids=['empty', 'none', 'yes', 'remark'],
)
def test_map_row_cover_letter(old, new):
    assert map_row({**OLD, 'coverLetter': old}, 0).cover_letter == new


def test_map_row_blank_optional_fields():
    body = map_row(
        {
            **OLD,
            'date': '',
            'approx': True,
            'salary': '  ',
            'notes': '',
            'location': '',
        },
        0,
    )
    assert body.applied_on is None
    assert body.is_approx is True
    assert body.salary_stated is None
    assert body.notes is None
    assert body.location is None


@pytest.mark.parametrize(
    ('field', 'value'),
    [
        ('country', '法國'),
        ('channel', 'Cake Resume'),
        ('status', '已錄取'),
        ('sponsor', '也許'),
    ],
)
def test_map_row_stops_on_unknown_value(field, value):
    with pytest.raises(RowError, match=re.escape(repr(value))) as info:
        map_row({**OLD, field: value}, 7)
    assert str(info.value).startswith('row 7: ')


@pytest.mark.parametrize('field', ['company', 'role'])
def test_map_row_stops_on_blank_name(field):
    with pytest.raises(RowError, match='row 3: '):
        map_row({**OLD, field: '  '}, 3)


@pytest.mark.parametrize(
    ('note', 'name'),
    [
        ('Roofoods Ltd t/a Deliveroo', 'Roofoods Ltd t/a Deliveroo'),
        ('Eui Limited（Admiral 的登記名稱）', 'Eui Limited'),
        ('Acme Ltd；母公司也在名單上', 'Acme Ltd'),
        ('Acme Ltd (UK Branch)', 'Acme Ltd'),
        ('Acme Ltd、Beta Ltd', 'Acme Ltd'),
        (
            'JPMorgan Chase Bank, National Association',
            'JPMorgan Chase Bank, National Association',
        ),
    ],
)
def test_sponsor_name_strips_remarks(note, name):
    assert sponsor_name(note) == name


def test_map_row_sponsor_statuses_and_remarks():
    agency = map_row({**OLD, 'sponsor': '獵頭', 'sponsorNote': '雇主未知'}, 0)
    assert agency.sponsor_check.status == 'agency'
    assert agency.sponsor_check.registered_name is None
    assert agency.notes == 'Applied via the careers page\n\nSponsor note: 雇主未知'

    not_found = map_row(
        {**OLD, 'notes': '', 'sponsor': '否', 'sponsorNote': '查不到'}, 0
    )
    assert not_found.sponsor_check.status == 'not_found'
    assert not_found.notes == 'Sponsor note: 查不到'

    remark = map_row(
        {**OLD, 'sponsor': '是', 'sponsorNote': 'Eui Limited（Admiral）'}, 0
    )
    assert remark.sponsor_check.status == 'on_list'
    assert remark.sponsor_check.registered_name == 'Eui Limited'
    assert remark.notes.endswith('Sponsor note: Eui Limited（Admiral）')

    plain = map_row({**OLD, 'sponsor': '是', 'sponsorNote': 'Eui Limited'}, 0)
    assert plain.sponsor_check.registered_name == 'Eui Limited'
    assert plain.notes == 'Applied via the careers page'


def test_import_links_sponsors_and_keeps_timestamps(
    session, importer, seed_sponsors, tmp_path
):
    seed_sponsors(
        extra_rows=[
            'Personio Group SE (UK Branch),London,,Worker (A rating),Skilled Worker'
        ]
    )
    rows = [
        {
            **OLD,
            'role': 'deliveroo',
            'sponsor': '是',
            'sponsorNote': 'Roofoods Ltd t/a Deliveroo',
        },
        {**OLD, 'role': 'admiral', 'sponsor': '是', 'sponsorNote': 'Admiral（別名）'},
        {**OLD, 'role': 'nowhere', 'sponsor': '是', 'sponsorNote': 'Nowhere Corp Ltd'},
        {**OLD, 'role': 'no', 'sponsor': '否', 'sponsorNote': '查不到'},
        {**OLD, 'role': 'agency', 'sponsor': '獵頭', 'sponsorNote': '雇主未知'},
        {**OLD, 'role': 'blank'},
        {
            **OLD,
            'role': 'bracket',
            'sponsor': '是',
            'sponsorNote': 'Personio Group SE (UK Branch)',
        },
    ]
    result = import_applications(session, _export(tmp_path, rows), EMAIL)
    assert result.total == 7
    assert result.existing == 0
    assert result.linked == 3
    assert result.unlinked == ['Nowhere Corp Ltd']
    assert result.by_country == {'UK': 7}
    assert result.by_status == {'applied': 7}

    checks = {
        row.role: row.sponsor_check
        for row in session.scalars(
            select(Application).where(Application.user_id == importer.id)
        )
    }
    assert checks['deliveroo']['status'] == 'on_list'
    assert checks['deliveroo']['match_type'] == 'exact'
    assert checks['deliveroo']['registered_name'] == 'Roofoods Ltd t/a Deliveroo'
    assert checks['deliveroo']['sponsor_id'] is not None
    assert checks['deliveroo']['register_published_on'] == '2026-10-16'
    assert checks['admiral']['match_type'] == 'alias'
    assert checks['admiral']['registered_name'] == 'Eui Limited'
    assert checks['nowhere'] == {
        **checks['nowhere'],
        'status': 'on_list',
        'sponsor_id': None,
        'registered_name': 'Nowhere Corp Ltd',
    }
    assert checks['no']['status'] == 'not_found'
    assert checks['agency']['status'] == 'agency'
    assert checks['blank']['status'] == 'unchecked'
    # the bracket is part of this legal name, so the whole note matched exactly
    assert checks['bracket']['match_type'] == 'exact'
    assert checks['bracket']['registered_name'] == 'Personio Group SE (UK Branch)'

    first = session.scalar(
        select(Application).where(
            Application.user_id == importer.id, Application.role == 'deliveroo'
        )
    )
    assert first.created_at == datetime.datetime(2026, 10, 13, 8, 50, 10, tzinfo=UTC)
    assert first.updated_at == datetime.datetime(2026, 10, 20, 2, 50, tzinfo=UTC)
    assert first.status_changed_at == first.updated_at


def test_import_needs_an_existing_user(session, tmp_path):
    with pytest.raises(LookupError, match=EMAIL):
        import_applications(session, _export(tmp_path, [OLD]), EMAIL)


def _old_row(session, user):
    session.add(
        Application(
            user_id=user.id,
            country='UK',
            company='Old Co',
            role='old role',
            work_mode='unknown',
            channel='other',
            status='applied',
            status_changed_at=datetime.datetime.now(UTC),
        )
    )
    session.flush()


def test_import_refuses_when_the_user_already_has_rows(session, importer, tmp_path):
    _old_row(session, importer)
    with pytest.raises(RuntimeError, match='already has 1'):
        import_applications(session, _export(tmp_path, [OLD]), EMAIL)
    assert _count(session, importer) == 1


def test_import_replace_swaps_the_old_rows(session, importer, tmp_path):
    _old_row(session, importer)
    result = import_applications(
        session,
        _export(tmp_path, [OLD, {**OLD, 'role': 'second'}]),
        EMAIL,
        replace=True,
    )
    assert result.existing == 1
    roles = sorted(
        session.scalars(
            select(Application.role).where(Application.user_id == importer.id)
        )
    )
    assert roles == ['Backend engineer', 'second']


def test_import_dry_run_writes_nothing(session, importer, tmp_path):
    _old_row(session, importer)
    result = import_applications(
        session,
        _export(tmp_path, [OLD, {**OLD, 'role': 'second'}]),
        EMAIL,
        dry_run=True,
    )
    assert result.total == 2
    assert result.existing == 1
    assert _count(session, importer) == 1


def test_import_bad_row_writes_nothing(session, importer, tmp_path):
    rows = [OLD, {**OLD, 'channel': 'Cake Resume'}]
    with pytest.raises(RowError, match="row 1: channel: no mapping for 'Cake Resume'"):
        import_applications(session, _export(tmp_path, rows), EMAIL)
    assert _count(session, importer) == 0
