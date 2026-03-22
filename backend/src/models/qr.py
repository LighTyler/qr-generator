"""Модель QR-токена.

Хранит информацию о токене для QR-авторизации.
Токен привязан к WebSocket-соединению через connection_id.
При разрыве соединения токен автоматически инвалидируется.
"""

from datetime import datetime

from sqlalchemy import String, func, Integer
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class QR(Base):
    """QR-токен для авторизации.
    
    Attributes:
        user_id: ID пользователя (primary key для поиска)
        username: Имя пользователя
        email: Email пользователя
        salt: Секретная часть токена
        timestamp: Время создания
        connection_id: ID WebSocket-соединения для инвалидации при разрыве
    """
    
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