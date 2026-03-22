"""
Начальная миграция: создание таблицы qr.

Создаёт таблицу для хранения QR-токенов авторизации.

Revision ID: a1b2c3d4e5f6
Revises: None (первая миграция)
Create Date: 2026-03-20 21:00:00.000000

Таблица qr содержит:
- id: автоинкрементный первичный ключ
- username: имя пользователя
- email: email пользователя (уникальный)
- salt: соль для хеширования приватной части токена
- timestamp: время создания токена
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# Идентификаторы ревизии для Alembic
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = None  # Первая миграция - нет предыдущей
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Применение миграции: создание таблицы qr.
    
    Создаёт таблицу с полями:
    - id: Integer, первичный ключ, автоинкремент
    - username: String(255), не может быть NULL
    - email: String(255), не может быть NULL, уникальный
    - salt: String(255), не может быть NULL
    - timestamp: DateTime, по умолчанию CURRENT_TIMESTAMP
    """
    op.create_table('qr',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('salt', sa.String(length=255), nullable=False),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')  # Уникальность email для привязки токена к пользователю
    )


def downgrade() -> None:
    """
    Откат миграции: удаление таблицы qr.
    
    Полностью удаляет таблицу qr из базы данных.
    Внимание: все данные будут потеряны!
    """
    op.drop_table('qr')
