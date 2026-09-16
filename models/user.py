from sqlalchemy import Identity, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer, Identity(always=True), primary_key=True
    )
    username: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
