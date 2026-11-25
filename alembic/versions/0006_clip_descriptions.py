"""Add English text descriptions for CLIP retrieval."""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

DESCRIPTIONS = {
    "TRAPPIST-1": "A red dwarf star surrounded by seven rocky planets in a dark star field.",
    "Kepler-186": "An orange rocky Earth-sized planet orbiting a distant red dwarf star.",
    "Проксима Центавра": "A bright red star with a rocky planet and a hazy red horizon in space.",
    "TOI-700": "A blue and green rocky planet and smaller planets around a dim red star.",
    "Gliese 667 C": "Three glowing stars in a multiple star system with a rocky planet.",
    "Kepler-442": "A distant orange star illuminating a rocky planet with a pale atmosphere.",
}


def upgrade():
    op.add_column("stars", sa.Column("clip_description", sa.String(100)))
    for title, description in DESCRIPTIONS.items():
        op.execute(sa.text(
            "UPDATE stars SET clip_description = :description WHERE lower(title) = lower(:title)"
        ).bindparams(title=title, description=description))


def downgrade():
    op.drop_column("stars", "clip_description")
