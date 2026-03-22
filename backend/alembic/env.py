"""
Конфигурация Alembic для управления миграциями базы данных.

Этот модуль настраивает окружение для выполнения миграций SQLAlchemy.
Поддерживает асинхронное подключение к PostgreSQL через asyncpg.

Режимы работы:
- Offline: генерация SQL без подключения к БД (для DBA)
- Online: выполнение миграций с подключением к БД

Использование:
    alembic revision --autogenerate -m "description"  # Создание миграции
    alembic upgrade head                               # Применение миграций
    alembic downgrade -1                               # Откат миграции
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Импорт базовой модели и всех моделей для autogenerate
from models.base import Base
from models.qr import QR  # noqa: F401 - нужен для регистрации модели в metadata
from entrypoint.config import config as _config

# Объект конфигурации Alembic (из alembic.ini)
config = context.config

# Устанавливаем URL базы данных из конфигурации приложения
config.set_main_option("sqlalchemy.url", _config.database.get_db_url())

# Настройка логирования из alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata моделей для автоматической генерации миграций
# При autogenerate Alembic сравнивает это metadata с состоянием БД
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Запуск миграций в 'offline' режиме.
    
    Этот режим конфигурирует контекст только с URL без создания Engine.
    Полезно когда нужно сгенерировать SQL скрипты без подключения к БД.
    
    Вызовы context.execute() отправляют SQL в выходной файл,
    а не выполняются в БД.
    
    Использование:
        alembic upgrade head --sql > migration.sql
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    Выполнение миграций в синхронном контексте.
    
    Настраивает контекст Alembic с подключением и запускает миграции.
    
    Args:
        connection: SQLAlchemy соединение с БД
    """
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Запуск миграций в асинхронном режиме.
    
    Создаёт асинхронный Engine и выполняет миграции.
    Использует NullPool для создания нового соединения при каждом запуске
    (избегает проблем с транзакциями в асинхронном режиме).
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # Без пула соединений для миграций
    )

    async with connectable.connect() as connection:
        # Выполняем миграции в синхронном контексте через run_sync
        await connection.run_sync(do_run_migrations)

    # Закрываем engine после выполнения
    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Запуск миграций в 'online' режиме.
    
    Подключается к БД и выполняет миграции.
    Использует asyncio.run для запуска асинхронной функции.
    """
    asyncio.run(run_async_migrations())


# Определение режима работы и запуск соответствующей функции
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
