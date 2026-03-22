"""
Модель пользователя системы.

Содержит информацию о пользователях, включая аутентификационные данные,
роль и настройки двухфакторной аутентификации.
"""

import enum

from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class RoleEnum(str, enum.Enum):
    """
    Перечисление ролей пользователей.
    
    Attributes:
        USER: Обычный пользователь системы
        ADMIN: Администратор с расширенными правами
    """
    USER = "user"
    ADMIN = "admin"


class User(Base):
    """
    Модель пользователя для хранения в базе данных.
    
    Наследуется от Base и использует таблицу 'users'.
    
    Attributes:
        username (str): Имя пользователя (обязательно)
        email (str): Email пользователя (обязательно, уникально)
        password (str): Хешированный пароль пользователя (обязательно)
        role (str): Роль пользователя (по умолчанию 'user')
        email_verified (bool): Флаг подтверждения email (по умолчанию False)
        token (str | None): Токен для различных операций (сброс пароля и т.д.)
        otp_secret (str | None): Секретный ключ для двухфакторной аутентификации
    
    Note:
        Пароль должен храниться в хешированном виде, никогда в открытом
    """
    __tablename__ = "users"

    # Имя пользователя
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Email - уникальный идентификатор для входа
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    
    # Хешированный пароль (никогда не хранить в открытом виде!)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Роль пользователя для разграничения прав доступа
    role: Mapped[str] = mapped_column(String(50), nullable=False, default=RoleEnum.USER.value)
    
    # Флаг подтверждения email адреса
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Токен для операций (сброс пароля, подтверждение email и т.д.)
    token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Секретный ключ для TOTP (Time-based One-Time Password) 2FA
    otp_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
