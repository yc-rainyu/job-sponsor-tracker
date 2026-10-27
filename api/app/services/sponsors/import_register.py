import csv
from datetime import date
from pathlib import Path
from typing import NamedTuple

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.orm import Session

from app.models.register import RegisterSnapshot, Sponsor, SponsorRoute
from app.services.sponsors.normalise import normalise_name

_BATCH = 1000


class ImportResult(NamedTuple):
    added: int
    removed: int
    total: int


# send rows in batches of 1000
def _chunks(rows: list, size: int = _BATCH):
    for start in range(0, len(rows), size):
        yield rows[start : start + size]


# collapse csv rows into orgs
def _read_csv(path: Path) -> tuple[int, dict]:
    orgs = {}
    row_count = 0
    with path.open(encoding='utf-8-sig', newline='') as csv_file:
        for row in csv.DictReader(csv_file):
            row_count += 1
            name_raw = row['Organisation Name'].strip()
            town = row['Town/City'].strip() or None
            county = row['County'].strip() or None
            key = (name_raw, town)
            org = orgs.get(key)
            if org is None:
                legal_norm, trading_raw, trading_norm = normalise_name(name_raw)
                org = {
                    'name_raw': name_raw,
                    'town': town,
                    'county': county,
                    'legal_name_norm': legal_norm,
                    'trading_name_raw': trading_raw,
                    'trading_name_norm': trading_norm,
                    'routes': set(),
                }
                orgs[key] = org
            org['routes'].add((row['Route'].strip(), row['Type & Rating'].strip()))
    return row_count, orgs


# upsert by diffing in python rather than ON CONFLICT, so we can count
# who is new, who is back on the register and who has gone
def import_register(
    session: Session, csv_path: Path | str, published: date
) -> ImportResult:
    csv_path = Path(csv_path)
    row_count, orgs = _read_csv(csv_path)

    snapshot = RegisterSnapshot(
        published_date=published,
        source_file=csv_path.name,
        row_count=row_count,
        org_count=len(orgs),
        added_count=0,
        removed_count=0,
    )
    session.add(snapshot)
    session.flush()

    existing = {
        (name, town): (sponsor_id, removed_time)
        for sponsor_id, name, town, removed_time in session.execute(
            select(
                Sponsor.id,
                Sponsor.name_raw,
                Sponsor.town,
                Sponsor.removed_time,
            )
        )
    }

    added = 0
    new_rows = []
    updates = []
    for key, org in orgs.items():
        previous = existing.get(key)
        if previous is None:
            added += 1
            new_rows.append(
                {
                    'name_raw': org['name_raw'],
                    'town': org['town'],
                    'county': org['county'],
                    'legal_name_norm': org['legal_name_norm'],
                    'trading_name_raw': org['trading_name_raw'],
                    'trading_name_norm': org['trading_name_norm'],
                    'first_seen_snapshot_id': snapshot.id,
                    'last_seen_snapshot_id': snapshot.id,
                }
            )
        else:
            sponsor_id, removed_time = previous
            if removed_time is not None:
                added += 1
            updates.append(
                {
                    'id': sponsor_id,
                    'county': org['county'],
                    'legal_name_norm': org['legal_name_norm'],
                    'trading_name_raw': org['trading_name_raw'],
                    'trading_name_norm': org['trading_name_norm'],
                    'last_seen_snapshot_id': snapshot.id,
                    'removed_time': None,
                }
            )

    for chunk in _chunks(new_rows):
        session.execute(insert(Sponsor), chunk)
    for chunk in _chunks(updates):
        session.execute(update(Sponsor), chunk)
    session.flush()

    id_by_key = {
        (name, town): sponsor_id
        for sponsor_id, name, town in session.execute(
            select(Sponsor.id, Sponsor.name_raw, Sponsor.town)
        )
    }

    session.execute(
        delete(SponsorRoute).where(
            SponsorRoute.sponsor_id.in_(
                select(Sponsor.id).where(Sponsor.last_seen_snapshot_id == snapshot.id)
            )
        )
    )
    route_rows = [
        {'sponsor_id': id_by_key[key], 'route': route, 'type_rating': rating}
        for key, org in orgs.items()
        for route, rating in org['routes']
    ]
    for chunk in _chunks(route_rows):
        session.execute(insert(SponsorRoute), chunk)

    removed = session.execute(
        update(Sponsor)
        .where(Sponsor.last_seen_snapshot_id != snapshot.id)
        .where(Sponsor.removed_time.is_(None))
        .values(removed_time=func.now())
    ).rowcount

    total = session.scalar(
        select(func.count()).select_from(Sponsor).where(Sponsor.removed_time.is_(None))
    )

    snapshot.added_count = added
    snapshot.removed_count = removed
    session.flush()

    return ImportResult(added=added, removed=removed, total=total)
