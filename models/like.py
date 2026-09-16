from sqlalchemy import ForeignKey, Identity, Integer
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base


class Like(Base):
    __tablename__ = "likes"

    id: Mapped[int] = mapped_column(
        Integer, Identity(always=True), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT", name="likes_user_fk"),
        nullable=False,
    )
    star_id: Mapped[int] = mapped_column(
        ForeignKey("stars.id", ondelete="RESTRICT", name="likes_star_fk"),
        nullable=False,
    )
