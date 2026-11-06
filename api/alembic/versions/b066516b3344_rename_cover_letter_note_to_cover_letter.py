"""rename cover_letter_note to cover_letter

Revision ID: b066516b3344
Revises: 17bb58fa63df
Create Date: 2026-11-06 14:50:35.690116

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b066516b3344'
down_revision: str | Sequence[str] | None = '17bb58fa63df'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column('applications', 'cover_letter_note', new_column_name='cover_letter')


def downgrade() -> None:
    op.alter_column('applications', 'cover_letter', new_column_name='cover_letter_note')
