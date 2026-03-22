import enum

from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class RoleEnum(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default=RoleEnum.USER.value)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    otp_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
