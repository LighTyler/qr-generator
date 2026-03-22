"""
Миграция: добавление полей connection_id и user_id в таблицу qr.

Добавляет поля для привязки QR-токена к WebSocket-соединению и пользователю.
Это позволяет инвалидировать токен при разрыве WebSocket-соединения.

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-22 05:15:00.000000

Новые поля:
- user_id: ID пользователя (уникальный, для поиска токена по пользователю)
- connection_id: ID WebSocket-соединения (для инвалидации при разрыве)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Идентификаторы ревизии для Alembic
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'  # Предыдущая миграция
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Применение миграции: добавление полей user_id и connection_id.
    
    1. Добавляет user_id - уникальный идентификатор пользователя
       (nullable=True для существующих записей)
    2. Добавляет connection_id - ID WebSocket-соединения
       (nullable=True, т.к. может быть не задан)
    3. Создаёт уникальное ограничение на user_id для быстрого поиска
    """
    # Добавляем user_id (сначала nullable для существующих записей)
    op.add_column('qr', sa.Column('user_id', sa.Integer(), nullable=True))
    
    # Добавляем connection_id для привязки к WebSocket
    op.add_column('qr', sa.Column('connection_id', sa.String(length=255), nullable=True))
    
    # Создаём уникальное ограничение на user_id
    # (один пользователь = один активный QR-токен)
    op.create_unique_constraint('uq_qr_user_id', 'qr', ['user_id'])


def downgrade() -> None:
    """
    Откат миграции: удаление полей user_id и connection_id.
    
    Удаляет добавленные поля и ограничение в обратном порядке.
    """
    # Удаляем уникальное ограничение
    op.drop_constraint('uq_qr_user_id', 'qr', type_='unique')
    
    # Удаляем колонки
    op.drop_column('qr', 'connection_id')
    op.drop_column('qr', 'user_id')
