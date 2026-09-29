"""cohorts

Revision ID: 003
Revises: 002
Create Date: 2026-09-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('submissions', sa.Column('cohort_id', sa.String(), nullable=True))
    op.create_table(
        'collusion_cache',
        sa.Column('cohort_id', sa.String(), nullable=False),
        sa.Column('doc_ids_hash', sa.String(), nullable=False),
        sa.Column('report', sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint('cohort_id')
    )


def downgrade() -> None:
    op.drop_table('collusion_cache')
    op.drop_column('submissions', 'cohort_id')
