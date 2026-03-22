"""add connection_id and user_id to qr table

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-22 05:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add connection_id and user_id columns to qr table."""
    # Добавляем user_id
    op.add_column('qr', sa.Column('user_id', sa.Integer(), nullable=True))
    
    # Добавляем connection_id
    op.add_column('qr', sa.Column('connection_id', sa.String(length=255), nullable=True))
    
    # Создаём уникальный индекс на user_id
    op.create_unique_constraint('uq_qr_user_id', 'qr', ['user_id'])


def downgrade() -> None:
    """Remove connection_id and user_id columns from qr table."""
    op.drop_constraint('uq_qr_user_id', 'qr', type_='unique')
    op.drop_column('qr', 'connection_id')
    op.drop_column('qr', 'user_id')
