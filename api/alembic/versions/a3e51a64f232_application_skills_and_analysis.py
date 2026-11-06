"""application skills and analysis

Revision ID: a3e51a64f232
Revises: b066516b3344
Create Date: 2026-11-07 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a3e51a64f232'
down_revision: str | Sequence[str] | None = 'b066516b3344'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'applications',
        sa.Column(
            'skills',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default='{"required": [], "nice_to_have": []}',
            nullable=False,
        ),
    )
    op.add_column(
        'applications',
        sa.Column('analysis', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('applications', 'analysis')
    op.drop_column('applications', 'skills')
