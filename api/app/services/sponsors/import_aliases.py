import csv
from pathlib import Path
from typing import NamedTuple

from sqlalchemy import func, insert, select
from sqlalchemy.orm import Session

from app.models.register import Sponsor, SponsorAlias
from app.services.sponsors.normalise import normalise_name


class AliasResult(NamedTuple):
    added: int
    total: int


# read alias, name, town
def _read_csv(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding='utf-8-sig', newline='') as f:
        for row in csv.DictReader(f):
            alias_norm, _, _ = normalise_name(row['alias'])
            rows.append(
                {
                    'alias_norm': alias_norm,
                    'name': row['name'].strip(),
                    'town': row['town'].strip() or None,
                }
            )
    return rows


# map brand names onto sponsors already on the register
def import_aliases(session: Session, csv_path: Path | str) -> AliasResult:
    csv_path = Path(csv_path)
    rows = _read_csv(csv_path)

    existing = set(session.scalars(select(SponsorAlias.alias_norm)))
    missing = []
    new_rows = []
    seen = set(existing)
    for row in rows:
        if row['alias_norm'] in seen:
            continue
        q = select(Sponsor.id).where(Sponsor.name_raw == row['name'])
        if row['town'] is None:
            ids = session.scalars(q).all()
        else:
            ids = session.scalars(q.where(Sponsor.town == row['town'])).all()
        if len(ids) != 1:
            missing.append(row)
            continue
        seen.add(row['alias_norm'])
        new_rows.append(
            {
                'alias_norm': row['alias_norm'],
                'sponsor_id': ids[0],
                'source': 'seed',
            }
        )

    if missing:
        bits = [
            f'{row["name"]} ({row["town"]})' if row['town'] else row['name']
            for row in missing
        ]
        raise ValueError('could not match ' + ', '.join(bits))

    if new_rows:
        session.execute(insert(SponsorAlias), new_rows)
        session.flush()

    total = session.scalar(select(func.count()).select_from(SponsorAlias))
    return AliasResult(added=len(new_rows), total=total)
