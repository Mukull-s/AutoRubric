"""initial

Revision ID: 001
Revises: 
Create Date: 2023-10-24 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # P3 will add vector tables in a separate migration file
    op.create_table('users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username')
    )
    op.create_table('rubrics',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('data', JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('submissions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('rubric_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('jobs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('submission_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('error', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('results',
        sa.Column('doc_id', sa.String(), nullable=False),
        sa.Column('rubric_id', sa.String(), nullable=False),
        sa.Column('data', JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('total_score', sa.Float(), nullable=False),
        sa.Column('needs_review', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('doc_id')
    )

def downgrade() -> None:
    op.drop_table('results')
    op.drop_table('jobs')
    op.drop_table('submissions')
    op.drop_table('rubrics')
    op.drop_table('users')
