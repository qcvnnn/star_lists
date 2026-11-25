"""Cover alternative star names in the existing catalog."""
from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None

ALIASES = {
    "Proxima Centauri": "A bright red star with a rocky planet and a hazy red horizon in space.",
    "Gliese 667": "Three glowing stars in a multiple star system with a rocky planet.",
}


def upgrade():
    for title, description in ALIASES.items():
        op.execute(sa.text(
            "UPDATE stars SET clip_description = :description "
            "WHERE lower(title) = lower(:title) AND clip_description IS NULL"
        ).bindparams(title=title, description=description))


def downgrade():
    for title, description in ALIASES.items():
        op.execute(sa.text(
            "UPDATE stars SET clip_description = NULL "
            "WHERE lower(title) = lower(:title) AND clip_description = :description"
        ).bindparams(title=title, description=description))
