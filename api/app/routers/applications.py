import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.applications import (
    Application,
    ApplicationCreate,
    ApplicationUpdate,
    Country,
    SponsorStatus,
    Status,
)
from app.services import applications

router = APIRouter()

Db = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get('/applications')
def list_applications(
    session: Db,
    user: CurrentUser,
    country: Country | None = None,
    status: Status | None = None,
    sponsor_status: SponsorStatus | None = None,
    q: Annotated[str | None, Query(max_length=200)] = None,
) -> list[Application]:
    rows = applications.list_applications(
        session,
        user,
        country=country,
        status=status,
        sponsor_status=sponsor_status,
        q=q,
    )
    return [Application.model_validate(row) for row in rows]


@router.post('/applications', status_code=201)
def create_application(
    body: ApplicationCreate, session: Db, user: CurrentUser
) -> Application:
    return Application.model_validate(
        applications.create_application(session, user, body)
    )


# declared before /applications/{application_id}, or "export.csv" would be read as an id
@router.get(
    '/applications/export.csv',
    response_class=Response,
    responses={200: {'content': {'text/csv': {}}}},
)
def export_applications(
    session: Db,
    user: CurrentUser,
    country: Country | None = None,
    status: Status | None = None,
    sponsor_status: SponsorStatus | None = None,
    q: Annotated[str | None, Query(max_length=200)] = None,
) -> Response:
    rows = applications.list_applications(
        session,
        user,
        country=country,
        status=status,
        sponsor_status=sponsor_status,
        q=q,
    )
    return Response(
        applications.export_csv(rows),
        media_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="applications.csv"'},
    )


@router.get('/applications/{application_id}')
def get_application(
    application_id: uuid.UUID, session: Db, user: CurrentUser
) -> Application:
    return Application.model_validate(
        applications.get_application(session, user, application_id)
    )


@router.patch('/applications/{application_id}')
def update_application(
    application_id: uuid.UUID,
    body: ApplicationUpdate,
    session: Db,
    user: CurrentUser,
) -> Application:
    return Application.model_validate(
        applications.update_application(session, user, application_id, body)
    )


@router.delete('/applications/{application_id}', status_code=204)
def delete_application(
    application_id: uuid.UUID, session: Db, user: CurrentUser
) -> None:
    applications.delete_application(session, user, application_id)
