"""enable pg_team

Revision ID: b04c2f5e1037
Revises:
Create Date: 2026-10-17 22:37:19.663591

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b04c2f5e1037'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')


def downgrade() -> None:
    op.execute('DROP EXTENSION IF EXISTS pg_trgm')
