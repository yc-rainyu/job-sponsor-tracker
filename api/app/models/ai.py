import datetime
import uuid
from typing import Any

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class JdAnalysis(Base):
    __tablename__ = 'jd_analyses'
    __table_args__ = (UniqueConstraint('text_sha256', 'model'),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    text_sha256: Mapped[str]
    model: Mapped[str]
    result: Mapped[dict[str, Any]] = mapped_column(JSONB)
    input_tokens: Mapped[int]
    output_tokens: Mapped[int]
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AiUsage(Base):
    __tablename__ = 'ai_usage'

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True
    )
    used_on: Mapped[datetime.date] = mapped_column(primary_key=True)
    count: Mapped[int] = mapped_column(default=0, server_default='0')
