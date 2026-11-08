import csv
import datetime
import io
import uuid

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models.application import Application
from app.models.user import User
from app.schemas.applications import ApplicationCreate, ApplicationUpdate

CSV_COLUMNS = [
    'applied_on',
    'is_approx',
    'country',
    'company',
    'role',
    'location',
    'work_mode',
    'channel',
    'status',
    'status_changed_at',
    'sponsor_status',
    'sponsor_registered_name',
    'salary_stated',
    'cover_letter',
    'next_step',
    'next_step_at',
    'job_url',
    'notes',
    'created_at',
    'updated_at',
]


_FORMULA_START = ('=', '+', '-', '@', '\t', '\r')


def _csv_cell(value: object) -> object:
    if isinstance(value, datetime.date):
        return value.isoformat()
    if isinstance(value, str) and value.startswith(_FORMULA_START):
        # a leading quote keeps it as text
        return "'" + value
    return value


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


def list_applications(
    session: Session,
    user: User,
    *,
    country: str | None = None,
    status: str | None = None,
    sponsor_status: str | None = None,
    q: str | None = None,
) -> list[Application]:
    query = select(Application).where(Application.user_id == user.id)
    if country:
        query = query.where(Application.country == country)
    if status:
        query = query.where(Application.status == status)
    if sponsor_status:
        query = query.where(
            Application.sponsor_check['status'].astext == sponsor_status
        )
    if q:
        query = query.where(
            or_(
                Application.company.icontains(q, autoescape=True),
                Application.role.icontains(q, autoescape=True),
                Application.location.icontains(q, autoescape=True),
                Application.notes.icontains(q, autoescape=True),
            )
        )
    query = query.order_by(
        Application.applied_on.desc().nulls_last(), Application.created_at.desc()
    )
    return list(session.scalars(query))


def get_application(
    session: Session, user: User, application_id: uuid.UUID
) -> Application:
    application = session.scalar(
        select(Application).where(
            Application.id == application_id, Application.user_id == user.id
        )
    )
    if application is None:
        # same answer for someone else's record, so ids cannot be probed
        raise HTTPException(status_code=404, detail='Application not found.')
    return application


def create_application(
    session: Session, user: User, body: ApplicationCreate
) -> Application:
    limit = (
        settings.demo_application_limit if user.is_demo else settings.application_limit
    )
    count = session.scalar(
        select(func.count())
        .select_from(Application)
        .where(Application.user_id == user.id)
    )
    if count >= limit:
        raise HTTPException(
            status_code=429,
            detail=f'This account can hold up to {limit} applications. '
            'Delete some to add more.',
        )
    values = body.model_dump()
    # JSONB cannot hold datetime objects, so store the JSON form
    values['sponsor_check'] = body.sponsor_check.model_dump(mode='json')
    application = Application(user_id=user.id, status_changed_at=_now(), **values)
    session.add(application)
    session.commit()
    session.refresh(application)
    return application


def update_application(
    session: Session, user: User, application_id: uuid.UUID, body: ApplicationUpdate
) -> Application:
    application = get_application(session, user, application_id)
    values = body.model_dump(exclude_unset=True)
    if body.sponsor_check is not None:
        values['sponsor_check'] = body.sponsor_check.model_dump(mode='json')
    if 'status' in values and values['status'] != application.status:
        application.status_changed_at = _now()
    for field, value in values.items():
        setattr(application, field, value)
    session.commit()
    session.refresh(application)
    return application


def delete_application(session: Session, user: User, application_id: uuid.UUID) -> None:
    application = get_application(session, user, application_id)
    session.delete(application)
    session.commit()


def export_csv(applications: list[Application]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS)
    writer.writeheader()
    for application in applications:
        row = {column: getattr(application, column, None) for column in CSV_COLUMNS}
        row['sponsor_status'] = application.sponsor_check.get('status')
        row['sponsor_registered_name'] = application.sponsor_check.get(
            'registered_name'
        )
        writer.writerow({column: _csv_cell(value) for column, value in row.items()})
    return buffer.getvalue()
