"""Add a plain-text password for the local educational example."""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("password", sa.String(20), nullable=True))
    op.execute("UPDATE users SET password = 'demo' || id::text || 'pass'")
    op.alter_column("users", "password", existing_type=sa.String(20), nullable=False)


def downgrade():
    op.drop_column("users", "password")
