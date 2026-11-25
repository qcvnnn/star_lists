"""Index the published catalog by received date and ID."""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "stars_catalog_received_date_idx", "stars", ["received_date", "id"],
        postgresql_where=sa.text("status = 'Опубликован'"),
    )


def downgrade():
    op.drop_index("stars_catalog_received_date_idx", table_name="stars")
