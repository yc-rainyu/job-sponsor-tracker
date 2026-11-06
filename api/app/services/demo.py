import datetime
import json
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.register import RegisterSnapshot, Sponsor
from app.models.user import User
from app.schemas.applications import ApplicationCreate, SponsorCheck

# repo root data/, which the Dockerfile copies to /data next to /app
SEED_PATH = Path(__file__).resolve().parents[3] / 'data' / 'demo-seed.json'
DEMO_LIFETIME = datetime.timedelta(hours=24)


def load_seed() -> list[ApplicationCreate]:
    rows = json.loads(SEED_PATH.read_text())
    return [ApplicationCreate.model_validate(row) for row in rows]


def create_demo_user(session: Session, today: datetime.date | None = None) -> User:
    now = datetime.datetime.now(datetime.UTC)
    if today is None or abs((today - now.date()).days) > 1:
        today = now.date()
    session.execute(
        delete(User).where(User.is_demo, User.created_at < now - DEMO_LIFETIME)
    )
    user = User(is_demo=True, display_name='Demo user', last_login_at=now)
    session.add(user)
    session.flush()
    for values in _seed_rows(session, now, today):
        session.add(Application(user_id=user.id, **values))
    session.commit()
    return user


def _seed_rows(
    session: Session,
    now: datetime.datetime,
    today: datetime.date,
) -> list[dict[str, Any]]:
    seed = load_seed()
    shift = today - max(row.applied_on for row in seed if row.applied_on)
    published_on = session.scalar(
        select(RegisterSnapshot.published_date)
        .order_by(RegisterSnapshot.id.desc())
        .limit(1)
    )
    rows = []
    for row in seed:
        values = row.model_dump()
        if row.applied_on:
            values['applied_on'] = row.applied_on + shift
        if row.next_step_at:
            values['next_step_at'] = row.next_step_at + shift
        values['status_changed_at'] = (
            datetime.datetime.combine(
                values['applied_on'], datetime.time(9), datetime.UTC
            )
            if values['applied_on']
            else now
        )
        values['sponsor_check'] = _sponsor_check(
            session, row.sponsor_check, now, published_on
        )
        rows.append(values)
    return rows


def _sponsor_check(
    session: Session,
    check: SponsorCheck,
    now: datetime.datetime,
    published_on: datetime.date | None,
) -> dict[str, Any]:
    updates: dict[str, Any] = {}
    if check.registered_name is not None:
        # sponsor ids differ between databases, so the seed names the row instead
        updates['sponsor_id'] = session.scalar(
            select(Sponsor.id).where(
                Sponsor.name_raw == check.registered_name, Sponsor.town == check.town
            )
        )
    if check.status != 'unchecked':
        updates['checked_at'] = now
    if check.status in ('on_list', 'not_found'):
        updates['register_published_on'] = published_on
    return check.model_copy(update=updates).model_dump(mode='json')
