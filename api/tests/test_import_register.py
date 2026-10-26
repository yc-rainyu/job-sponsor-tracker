from datetime import date
from pathlib import Path

from sqlalchemy import select

from app.models.register import RegisterSnapshot, Sponsor, SponsorRoute
from app.services.sponsors.import_register import import_register

HEADER = 'Organisation Name,Town/City,County,Type & Rating,Route'
PUBLISHED = date(2026, 10, 16)

V1 = [
    'Roofoods Ltd t/a Deliveroo,London,,Worker (A rating),Skilled Worker',
    'Roofoods Ltd t/a Deliveroo,London,,Worker (A rating),Intra-Company Routes',
    ' AaruvikA Limited,Edinburgh,,Worker (A rating),Skilled Worker',
    'Marks & Spencer PLC,London,,Worker (A rating),Skilled Worker',
    'Marks & Spencer PLC,London,,Worker (A rating),Skilled Worker',
    'Solo Trader Ltd,,,Worker (A rating),Skilled Worker',
]

V2 = [
    'Roofoods Ltd t/a Deliveroo,London,,Worker (A rating),Skilled Worker',
    'Marks & Spencer PLC,London,,Worker (A rating),Skilled Worker',
    'Solo Trader Ltd,,,Worker (A rating),Skilled Worker',
    'Stripe Payments UK Ltd,London,,Worker (A rating),Skilled Worker',
]


def _write(tmp_path: Path, rows: list[str], *, bom: bool = False) -> Path:
    path = tmp_path / 'register.csv'
    path.write_text(
        HEADER + '\n' + '\n'.join(rows) + '\n',
        encoding='utf-8-sig' if bom else 'utf-8',
    )
    return path


def _sponsor(session, name: str) -> Sponsor:
    return session.scalars(select(Sponsor).where(Sponsor.name_raw == name)).one()


def _routes(session, sponsor_id: int) -> list[str]:
    return sorted(
        session.scalars(
            select(SponsorRoute.route).where(SponsorRoute.sponsor_id == sponsor_id)
        )
    )


# first load, collapse rows into orgs
def test_import(session, tmp_path):
    result = import_register(session, _write(tmp_path, V1), PUBLISHED)

    assert result.added == 4
    assert result.removed == 0
    assert result.total == 4

    snapshot = session.scalars(select(RegisterSnapshot)).one()
    assert snapshot.row_count == 6
    assert snapshot.org_count == 4
    assert snapshot.added_count == 4
    assert snapshot.removed_count == 0
    assert snapshot.published_date == PUBLISHED
    assert snapshot.source_file == 'register.csv'

    deliveroo = _sponsor(session, 'Roofoods Ltd t/a Deliveroo')
    assert deliveroo.legal_name_norm == 'roofoods ltd'
    assert deliveroo.trading_name_raw == 'Deliveroo'
    assert deliveroo.town == 'London'
    assert _routes(session, deliveroo.id) == [
        'Intra-Company Routes',
        'Skilled Worker',
    ]

    aaruvika = _sponsor(session, 'AaruvikA Limited')
    assert aaruvika.legal_name_norm == 'aaruvika ltd'
    assert aaruvika.town == 'Edinburgh'

    marks = _sponsor(session, 'Marks & Spencer PLC')
    assert marks.legal_name_norm == 'marks and spencer plc'
    assert _routes(session, marks.id) == ['Skilled Worker']

    solo = _sponsor(session, 'Solo Trader Ltd')
    assert solo.town is None


# same file again, ids must not change
def test_reimport(session, tmp_path):
    path = _write(tmp_path, V1)
    import_register(session, path, PUBLISHED)
    ids = {
        name: sponsor_id
        for name, sponsor_id in session.execute(select(Sponsor.name_raw, Sponsor.id))
    }

    result = import_register(session, path, PUBLISHED)
    session.expire_all()

    assert result.added == 0
    assert result.removed == 0
    assert result.total == 4
    assert {
        name: sponsor_id
        for name, sponsor_id in session.execute(select(Sponsor.name_raw, Sponsor.id))
    } == ids
    assert len(session.scalars(select(RegisterSnapshot)).all()) == 2


# gone from the new file, mark removed but keep the row
def test_removed(session, tmp_path):
    import_register(session, _write(tmp_path, V1), PUBLISHED)
    aaruvika_id = _sponsor(session, 'AaruvikA Limited').id
    deliveroo_id = _sponsor(session, 'Roofoods Ltd t/a Deliveroo').id

    result = import_register(session, _write(tmp_path, V2), date(2026, 11, 1))
    session.expire_all()

    assert result.added == 1
    assert result.removed == 1
    assert result.total == 4

    aaruvika = session.get(Sponsor, aaruvika_id)
    assert aaruvika.removed_time is not None
    assert aaruvika.name_raw == 'AaruvikA Limited'

    assert _sponsor(session, 'Stripe Payments UK Ltd').removed_time is None
    assert _sponsor(session, 'Roofoods Ltd t/a Deliveroo').removed_time is None
    assert _routes(session, deliveroo_id) == ['Skilled Worker']


# listed again, drop the removed flag
def test_back(session, tmp_path):
    import_register(session, _write(tmp_path, V1), PUBLISHED)
    import_register(session, _write(tmp_path, V2), date(2026, 11, 1))

    result = import_register(session, _write(tmp_path, V1), date(2026, 12, 1))
    session.expire_all()

    assert result.added == 1
    assert result.removed == 1
    assert _sponsor(session, 'AaruvikA Limited').removed_time is None
    assert _sponsor(session, 'Stripe Payments UK Ltd').removed_time is not None


# gov.uk csv starts with a BOM
def test_bom(session, tmp_path):
    result = import_register(session, _write(tmp_path, V1, bom=True), PUBLISHED)
    assert result.total == 4
    assert _sponsor(session, 'Roofoods Ltd t/a Deliveroo')
