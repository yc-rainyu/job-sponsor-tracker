import datetime

from sqlalchemy import DateTime, ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RegisterSnapshot(Base):
    __tablename__ = 'register_snapshots'

    id: Mapped[int] = mapped_column(primary_key=True)
    published_date: Mapped[datetime.date]
    source_file: Mapped[str]
    row_count: Mapped[int]
    org_count: Mapped[int]
    added_count: Mapped[int]
    removed_count: Mapped[int]
    import_time: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default = func.now()
    )

class Sponsor(Base):
    __tablename__ = 'sponsors'
    __table_args__ = (
        UniqueConstraint('name_raw', 'town', postgresql_nulls_not_distinct=True),
        Index(
            'ix_sponsor_legal_name_norm_trgm',
            'legal_name_norm',
            postgresql_using='gin',
            postgresql_ops={'legal_name_norm': 'gin_trgm_ops'},
        ),
        Index(
            'ix_sponsor_trading_name_norm_trgm',
            'trading_name_norm',
            postgresql_using = 'gin',
            postgresql_ops = {'trading_name_norm': 'gin_trgm_ops'},
        )
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name_raw: Mapped[str]
    legal_name_norm: Mapped[str]
    trading_name_raw: Mapped[str | None]
    trading_name_norm: Mapped[str | None]
    town: Mapped[str | None]
    county: Mapped[str | None]
    first_seen_snapshot_id: Mapped[int] = mapped_column(ForeignKey('register_snapshots.id'))
    last_seen_snapshot_id: Mapped[int] = mapped_column(ForeignKey('register_snapshots.id'))
    removed_time: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

class SponsorRoute(Base):
    __tablename__ = 'sponsor_routes'
    __table_args__ = (
        UniqueConstraint('sponsor_id', 'route', 'type_rating'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sponsor_id: Mapped[int] = mapped_column(ForeignKey('sponsors.id'))
    route: Mapped[str]
    type_rating: Mapped[str]

class SponsorAlias(Base):
    __tablename__ = 'sponsor_aliases'

    id: Mapped[int] = mapped_column(primary_key=True)
    alias_norm: Mapped[str]
    sponsor_id: Mapped[int] = mapped_column(ForeignKey('sponsors.id'))
    source: Mapped[str]