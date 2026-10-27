from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import select

from app.models.register import Sponsor, SponsorAlias
from app.services.sponsors.import_aliases import import_aliases
from app.services.sponsors.import_register import import_register

PUBLISHED = date(2026, 10, 16)
REGISTER_HEADER = 'Organisation Name,Town/City,County,Type & Rating,Route'
ALIAS_HEADER = 'alias,name,town'

REGISTER = [
    'Eui Limited,Cardiff,,Worker (A rating),Skilled Worker',
    'ESSO Petroleum Company Ltd,Leatherhead,Surrey,Worker (A rating),Skilled Worker',
]

ALIASES = [
    'Admiral,Eui Limited,Cardiff',
    'ExxonMobil,ESSO Petroleum Company Ltd,Leatherhead',
]


def _write(tmp_path: Path, header: str, rows: list[str], name: str) -> Path:
    path = tmp_path / name
    path.write_text(header + '\n' + '\n'.join(rows) + '\n')
    return path


def _load_register(session, tmp_path):
    import_register(
        session, _write(tmp_path, REGISTER_HEADER, REGISTER, 'register.csv'), PUBLISHED
    )


# first load, brand names point at the right orgs
def test_import(session, tmp_path):
    _load_register(session, tmp_path)
    result = import_aliases(
        session, _write(tmp_path, ALIAS_HEADER, ALIASES, 'aliases.csv')
    )

    assert result.added == 2
    assert result.total == 2

    eui = session.scalars(
        select(Sponsor).where(Sponsor.name_raw == 'Eui Limited')
    ).one()
    alias = session.scalars(
        select(SponsorAlias).where(SponsorAlias.alias_norm == 'admiral')
    ).one()
    assert alias.sponsor_id == eui.id
    assert alias.source == 'seed'

    esso = session.scalars(
        select(Sponsor).where(Sponsor.name_raw == 'ESSO Petroleum Company Ltd')
    ).one()
    exxon = session.scalars(
        select(SponsorAlias).where(SponsorAlias.alias_norm == 'exxonmobil')
    ).one()
    assert exxon.sponsor_id == esso.id


# same file again, no extra rows
def test_reimport(session, tmp_path):
    _load_register(session, tmp_path)
    path = _write(tmp_path, ALIAS_HEADER, ALIASES, 'aliases.csv')
    import_aliases(session, path)

    result = import_aliases(session, path)
    session.expire_all()

    assert result.added == 0
    assert result.total == 2
    assert len(session.scalars(select(SponsorAlias)).all()) == 2


# name not on the register, stop
def test_unknown(session, tmp_path):
    _load_register(session, tmp_path)
    path = _write(
        tmp_path,
        ALIAS_HEADER,
        ['GhostBrand,Nope Ltd,London'],
        'aliases.csv',
    )
    with pytest.raises(ValueError, match='could not match Nope Ltd'):
        import_aliases(session, path)
    assert session.scalars(select(SponsorAlias)).all() == []
