from datetime import datetime

from sqlalchemy import String, func, Integer
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class QR(Base):
    __tablename__ = "qr"
    
    user_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        unique=True,
    )
    username: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )
    salt: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(server_default=func.current_timestamp())
    connection_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
    )