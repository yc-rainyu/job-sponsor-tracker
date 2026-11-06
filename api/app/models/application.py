import datetime
import uuid
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Application(Base):
    __tablename__ = 'applications'

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey('users.id', ondelete='CASCADE'), index=True
    )
    applied_on: Mapped[datetime.date | None]
    is_approx: Mapped[bool] = mapped_column(default=False, server_default='false')
    country: Mapped[str]
    company: Mapped[str]
    role: Mapped[str]
    location: Mapped[str | None]
    work_mode: Mapped[str]
    channel: Mapped[str]
    status: Mapped[str]
    status_changed_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True)
    )
    salary_stated: Mapped[str | None]
    cover_letter: Mapped[str] = mapped_column(default='', server_default='')
    notes: Mapped[str | None]
    job_url: Mapped[str | None]
    jd_text: Mapped[str | None]
    next_step: Mapped[str | None]
    next_step_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    sponsor_check: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=lambda: {'status': 'unchecked'},
        server_default='{"status": "unchecked"}',
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
