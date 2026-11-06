import datetime
import json
import re
from pathlib import Path
from typing import Any, NamedTuple

from pydantic import ValidationError
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.register import RegisterSnapshot
from app.models.user import User
from app.schemas.applications import ApplicationCreate, SponsorCheck
from app.schemas.sponsors import SponsorResult
from app.services.sponsors.search import search_sponsors

# old tracker values on the left (spec appendix C); unknown values stop the import
COUNTRIES = {'英國': 'UK', '台灣': 'TW', '荷蘭': 'NL', '美國（遠端）': 'US'}
CHANNELS = {
    '': 'other',
    '104': 'job_board_104',
    'Cake': 'job_board_cake',
    '官網': 'company_site',
    '官網（從 LinkedIn 連過去）': 'company_site',
    '官網（LinkedIn 外）': 'company_site',
    'LinkedIn 一鍵應徵': 'linkedin_easy_apply',
    'Email': 'email',
    '主管主動邀約': 'other',
}
STATUSES = {
    '已送出': 'applied',
    '面試中': 'interviewing',
    '已拒絕': 'rejected',
    '待確認送出': 'draft',
}
SPONSORS = {
    None: 'unchecked',
    '': 'unchecked',
    '是': 'on_list',
    '否': 'not_found',
    '獵頭': 'agency',
}
NO_COVER_LETTER = {'', '無'}
# sponsor notes are registered names, often with a remark in brackets or after ';'
_REMARK = re.compile(r'[（(；;、]')


class RowError(ValueError):
    def __init__(self, index: int, message: str):
        super().__init__(f'row {index}: {message}')
        self.index = index


class ImportResult(NamedTuple):
    total: int
    existing: int
    by_country: dict[str, int]
    by_status: dict[str, int]
    linked: int
    unlinked: list[str]


def _lookup(mapping: dict[Any, str], index: int, field: str, value: Any) -> str:
    if value not in mapping:
        raise RowError(index, f'{field}: no mapping for {value!r}')
    return mapping[value]


def _blank(value: str | None) -> str | None:
    text = (value or '').strip()
    return text or None


def _timestamp(value: str) -> datetime.datetime:
    return datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))


def sponsor_name(note: str) -> str:
    return _REMARK.split(note, 1)[0].strip()


def map_row(old: dict[str, Any], index: int) -> ApplicationCreate:
    country = _lookup(COUNTRIES, index, 'country', old.get('country'))
    channel = _lookup(CHANNELS, index, 'channel', old.get('channel') or '')
    status = _lookup(STATUSES, index, 'status', old.get('status'))
    sponsor_status = _lookup(SPONSORS, index, 'sponsor', old.get('sponsor'))
    note = (old.get('sponsorNote') or '').strip()
    name = sponsor_name(note) if sponsor_status == 'on_list' else ''
    notes = _blank(old.get('notes'))
    # the remark has nowhere else to go, so it stays readable at the end of the notes
    if note and note != name:
        notes = f'{notes}\n\nSponsor note: {note}' if notes else f'Sponsor note: {note}'
    cover = (old.get('coverLetter') or '').strip()
    try:
        return ApplicationCreate(
            company=old.get('company') or '',
            role=old.get('role') or '',
            country=country,
            applied_on=(
                datetime.date.fromisoformat(old['date']) if old.get('date') else None
            ),
            is_approx=bool(old.get('approx')),
            location=_blank(old.get('location')),
            channel=channel,
            status=status,
            salary_stated=_blank(old.get('salary')),
            cover_letter='' if cover in NO_COVER_LETTER else cover,
            notes=notes,
            sponsor_check=SponsorCheck(
                status=sponsor_status, registered_name=name or None
            ),
        )
    except (ValidationError, ValueError) as exc:
        raise RowError(index, str(exc)) from exc


def _find_sponsor(session: Session, name: str) -> SponsorResult | None:
    hits, _total = search_sponsors(session, name, limit=1)
    # a fuzzy first hit is a guess: report the row and let the user pick in the ui
    if hits and hits[0].match_type in ('exact', 'alias'):
        return hits[0]
    return None


def import_applications(
    session: Session,
    path: Path | str,
    email: str,
    *,
    replace: bool = False,
    dry_run: bool = False,
) -> ImportResult:
    user = session.scalar(select(User).where(User.email == email))
    if user is None:
        raise LookupError(
            f'no user with email {email}; sign in once with that account first'
        )
    existing = (
        session.scalar(
            select(func.count())
            .select_from(Application)
            .where(Application.user_id == user.id)
        )
        or 0
    )
    if existing and not replace and not dry_run:
        raise RuntimeError(
            f'{email} already has {existing} applications; use --replace to delete them'
        )
    rows = json.loads(Path(path).read_text())
    published_on = session.scalar(
        select(RegisterSnapshot.published_date)
        .order_by(RegisterSnapshot.id.desc())
        .limit(1)
    )
    now = datetime.datetime.now(datetime.UTC)
    applications: list[Application] = []
    by_country: dict[str, int] = {}
    by_status: dict[str, int] = {}
    linked = 0
    unlinked: list[str] = []
    for index, old in enumerate(rows):
        body = map_row(old, index)
        check = body.sponsor_check
        if check.status == 'on_list':
            note = (old.get('sponsorNote') or '').strip()
            hit = None
            # brackets may be part of the legal name, so try the whole note first
            for candidate in dict.fromkeys([note, check.registered_name or '']):
                hit = _find_sponsor(session, candidate)
                if hit is not None:
                    break
            if hit is None:
                unlinked.append(check.registered_name or '')
                check = check.model_copy(
                    update={'checked_at': now, 'register_published_on': published_on}
                )
            else:
                linked += 1
                check = SponsorCheck(
                    status='on_list',
                    sponsor_id=hit.id,
                    registered_name=hit.registered_name,
                    town=hit.town,
                    match_type=hit.match_type,
                    score=hit.score,
                    has_skilled_worker=hit.has_skilled_worker,
                    rating=hit.rating,
                    checked_at=now,
                    register_published_on=published_on,
                )
        try:
            created_at = _timestamp(old['createdAt']) if old.get('createdAt') else now
            updated_at = _timestamp(old['updatedAt']) if old.get('updatedAt') else now
        except ValueError as exc:
            raise RowError(index, str(exc)) from exc
        values = body.model_dump()
        values['sponsor_check'] = check.model_dump(mode='json')
        applications.append(
            Application(
                user_id=user.id,
                status_changed_at=updated_at,
                created_at=created_at,
                updated_at=updated_at,
                **values,
            )
        )
        by_country[body.country] = by_country.get(body.country, 0) + 1
        by_status[body.status] = by_status.get(body.status, 0) + 1
    if not dry_run:
        if replace:
            session.execute(delete(Application).where(Application.user_id == user.id))
        session.add_all(applications)
        session.flush()
    return ImportResult(
        total=len(applications),
        existing=existing,
        by_country=by_country,
        by_status=by_status,
        linked=linked,
        unlinked=unlinked,
    )
