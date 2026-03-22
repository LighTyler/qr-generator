"""
Базовый класс для всех моделей SQLAlchemy.

Предоставляет общие поля и методы для всех моделей в проекте:
- id: автоинкрементный первичный ключ
- created_at: время создания записи
- updated_at: время последнего обновления записи
- автоматическая генерация имени таблицы во множественном числе
"""

import uuid
from datetime import datetime

import inflect
from sqlalchemy import Integer, func
from sqlalchemy import Integer, func, Uuid
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

# Движок inflect для преобразования слов во множественное число
p = inflect.engine()


class Base(AsyncAttrs, DeclarativeBase):
    """
    Абстрактный базовый класс для всех моделей.
    
    Наследует:
        - AsyncAttrs: поддержка асинхронной загрузки атрибутов
        - DeclarativeBase: базовый класс для декларативных моделей SQLAlchemy
    
    Атрибуты класса:
        __abstract__ (bool): указывает, что класс является абстрактным
                              и для него не создается таблица в БД
    
    Автоматически генерируемые поля:
        id: целочисленный первичный ключ с автоинкрементом
        created_at: timestamp создания записи (устанавливается БД)
        updated_at: timestamp обновления записи (обновляется БД автоматически)
    """
    __abstract__ = True

    # Первичный ключ - автоинкрементный integer
    id: Mapped[int] = mapped_column(
        Integer(),
        primary_key=True,
        autoincrement=True,
    )

    # Время создания записи - устанавливается БД при INSERT
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
    )
    
    # Время обновления записи - обновляется БД при каждом UPDATE
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """
        Автоматически генерирует имя таблицы из имени класса.
        
        Преобразует CamelCase в snake_case и добавляет множественное число.
        Например: User -> users, QRToken -> qr_tokens
        
        Returns:
            str: имя таблицы в snake_case во множественном числе
        """
        name = cls.__name__
        # Преобразование CamelCase в snake_case
        snake_case = "".join(
            ["_" + c.lower() if c.isupper() else c for c in name]
        ).lstrip("_")
        # Преобразование во множественное число
        plural = p.plural(snake_case)
        return plural

    def __repr__(self):
        """
        Строковое представление объекта для отладки.
        
        Returns:
            str: строка вида "<ClassName col1=val1,col2=val2,...>"
        """
        cols = []
        for num, col in enumerate(self.__table__.columns.keys()):
            cols.append(f"{col}={getattr(self, col)}")

        return f"<{self.__class__.__name__} {','.join(cols)}>"
