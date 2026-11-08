import datetime
import uuid

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str | None] = mapped_column(unique=True)
    display_name: Mapped[str | None]
    avatar_url: Mapped[str | None]
    is_demo: Mapped[bool] = mapped_column(default=False, server_default='false')
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_login_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True)
    )


class AuthIdentity(Base):
    __tablename__ = 'auth_identities'
    __table_args__ = (UniqueConstraint('provider', 'provider_subject'),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey('users.id', ondelete='CASCADE'), index=True
    )
    provider: Mapped[str]
    provider_subject: Mapped[str]
