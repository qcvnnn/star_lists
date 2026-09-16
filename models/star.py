from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Index,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class Star(Base):
    __tablename__ = "stars"
    __table_args__ = (
        CheckConstraint("status IN ('Черновик', 'Опубликован', 'Удален')", name="stars_status_check"),
        Index("stars_one_draft_per_user", "creator_id", unique=True,
              postgresql_where=text("status = 'Черновик'")),
    )

    id: Mapped[int] = mapped_column(
        Integer, Identity(always=True), primary_key=True
    )
    title: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'Черновик'"),
    )
    image_url: Mapped[str | None] = mapped_column(
        String(2048), nullable=True
    )
    video_url: Mapped[str | None] = mapped_column(
        String(2048), nullable=True
    )
    received_date: Mapped[date | None] = mapped_column(
        Date, nullable=True
    )
    habitable_planets: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    creator_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT", name="stars_creator_fk"),
        nullable=False,
    )
    formed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


