"""update_users_table_for_auth

Revision ID: 002
Revises: 001
Create Date: 2026-10-06 13:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Add new columns with defaults
    op.add_column('users', sa.Column('full_name', sa.String(), nullable=True))
    op.add_column('users', sa.Column('role', sa.String(), server_default='teacher', nullable=False))
    op.add_column('users', sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False))
    op.add_column('users', sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False))
    op.add_column('users', sa.Column('last_login_at', sa.DateTime(), nullable=True))

    # 2. Rename existing columns
    op.alter_column('users', 'username', new_column_name='email')
    op.alter_column('users', 'hashed_password', new_column_name='password_hash')

    # 3. Handle IDs if there are existing rows with non-uuid strings, and lowercase emails
    op.execute("UPDATE users SET id = gen_random_uuid()::text WHERE id !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'")
    op.execute("UPDATE users SET email = lower(email)")

    # 4. Change id type to UUID
    op.execute("ALTER TABLE users ALTER COLUMN id TYPE uuid USING id::uuid")

    # 5. Drop old unique constraint on username
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_username_key")

    # 6. Create unique index on lower(email)
    op.execute("CREATE UNIQUE INDEX ix_users_email_lower ON users (lower(email))")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_users_email_lower")
    
    op.execute("ALTER TABLE users ALTER COLUMN id TYPE character varying USING id::text")
    
    op.alter_column('users', 'email', new_column_name='username')
    op.alter_column('users', 'password_hash', new_column_name='hashed_password')
    
    op.create_unique_constraint('users_username_key', 'users', ['username'])
    
    op.drop_column('users', 'last_login_at')
    op.drop_column('users', 'created_at')
    op.drop_column('users', 'is_active')
    op.drop_column('users', 'role')
    op.drop_column('users', 'full_name')
