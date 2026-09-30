"""add job tracking and audit bundle

Revision ID: 002
Revises: 001
Create Date: 2023-10-25 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('job_events',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('job_id', sa.String(), nullable=False),
        sa.Column('stage', sa.String(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('ok', sa.Boolean(), nullable=True),
        sa.Column('error', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('job_artifacts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('job_id', sa.String(), nullable=False),
        sa.Column('stage', sa.String(), nullable=False),
        sa.Column('payload', JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('failed_jobs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('job_id', sa.String(), nullable=False),
        sa.Column('error', sa.String(), nullable=False),
        sa.Column('traceback', sa.String(), nullable=False),
        sa.Column('failed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.add_column('results', sa.Column('audit_bundle', JSONB(astext_type=sa.Text()), nullable=True))

def downgrade() -> None:
    op.drop_column('results', 'audit_bundle')
    op.drop_table('failed_jobs')
    op.drop_table('job_artifacts')
    op.drop_table('job_events')
