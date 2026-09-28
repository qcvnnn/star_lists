"""Require media URLs and use local defaults when omitted."""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    for column, default in (
        ("image_url", "/static/media/default-star.jpg"),
        ("video_url", "/static/media/default-star.mp4"),
    ):
        op.execute(
            sa.text(f"UPDATE stars SET {column} = :default "
                    f"WHERE {column} IS NULL OR btrim({column}) = ''")
            .bindparams(default=default)
        )
        op.alter_column("stars", column, existing_type=sa.String(2048),
                        nullable=False, server_default=default)


def downgrade():
    for column in ("image_url", "video_url"):
        op.alter_column("stars", column, existing_type=sa.String(2048),
                        nullable=True, server_default=None)
