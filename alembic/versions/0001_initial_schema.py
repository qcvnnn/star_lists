"""Existing stars, users and likes schema.

Revision ID: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("users",
        sa.Column("id", sa.Integer(), sa.Identity(always=True), primary_key=True),
        sa.Column("username", sa.String(50), nullable=False))
    op.create_table("stars",
        sa.Column("id", sa.Integer(), sa.Identity(always=True), primary_key=True),
        sa.Column("title", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'Черновик'")),
        sa.Column("image_url", sa.String(2048), nullable=True),
        sa.Column("video_url", sa.String(2048), nullable=True),
        sa.Column("received_date", sa.Date(), nullable=True),
        sa.Column("habitable_planets", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("creator_id", sa.Integer(), nullable=False),
        sa.Column("formed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('Черновик', 'Опубликован', 'Удален')", name="stars_status_check"),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"], name="stars_creator_fk", ondelete="RESTRICT"))
    op.create_index("stars_one_draft_per_user", "stars", ["creator_id"], unique=True,
                    postgresql_where=sa.text("status = 'Черновик'"))
    op.create_table("likes",
        sa.Column("id", sa.Integer(), sa.Identity(always=True), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("star_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="likes_user_fk", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["star_id"], ["stars.id"], name="likes_star_fk", ondelete="RESTRICT"))


def downgrade():
    op.drop_table("likes")
    op.drop_index("stars_one_draft_per_user", table_name="stars")
    op.drop_table("stars")
    op.drop_table("users")
