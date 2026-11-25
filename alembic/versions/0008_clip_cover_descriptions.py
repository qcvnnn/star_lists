"""Describe the actual catalog covers for text-to-image retrieval."""
from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None

DESCRIPTIONS = (
    ("TRAPPIST-1", "A brown rocky world with mottled continents, half lit against a dense star field.",
     "A red dwarf star surrounded by seven rocky planets in a dark star field."),
    ("TOI-700", "A smooth golden planet with a thin blue rim and a large shadow on its right side.",
     "A blue and green rocky planet and smaller planets around a dim red star."),
    ("Proxima Centauri", "A glowing red star with fiery clouds and a vivid orange ring in a dusty galaxy.",
     "A bright red star with a rocky planet and a hazy red horizon in space."),
    ("Gliese 667", "A blue and white Earth-like planet with swirling clouds and an icy gray hemisphere.",
     "Three glowing stars in a multiple star system with a rocky planet."),
)


def replace_descriptions(reverse=False):
    for title, cover, original in DESCRIPTIONS:
        new_value, old_value = (original, cover) if reverse else (cover, original)
        op.execute(sa.text(
            "UPDATE stars SET clip_description = :new "
            "WHERE lower(title) = lower(:title) AND clip_description = :old"
        ).bindparams(title=title, new=new_value, old=old_value))


def upgrade():
    replace_descriptions()


def downgrade():
    replace_descriptions(reverse=True)
