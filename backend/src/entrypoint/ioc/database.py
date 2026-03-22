"""
Провайдер подключения к базе данных для dependency injection.

Создаёт и управляет соединениями с PostgreSQL через SQLAlchemy async.
Предоставляет сессии БД для каждого HTTP запроса.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from entrypoint.config import config
from dishka import Provider, Scope, provide


class DatabaseProvider(Provider):
    """
    Провайдер подключения к базе данных.
    
    Создаёт асинхронный движок SQLAlchemy и фабрику сессий.
    Для каждого HTTP запроса предоставляется новая сессия.
    
    Scope: REQUEST - новая сессия на каждый запрос
    
    Attributes:
        engine: Асинхронный движок SQLAlchemy для подключения к PostgreSQL
        session_factory: Фабрика для создания асинхронных сессий
    
    Note:
        - expire_on_commit=False: объекты остаются доступными после коммита
        - autoflush=False: автоматический flush отключён для контроля
    """
    scope = Scope.REQUEST

    # Асинхронный движок для подключения к PostgreSQL
    engine = create_async_engine(
        config.database.get_db_url(),
        future=True,  # Использовать API SQLAlchemy 2.0
    )
    
    # Фабрика сессий для создания сессий в каждом запросе
    session_factory = async_sessionmaker(
        engine,
        expire_on_commit=False,  # Объекты доступны после commit
        autoflush=False,  # Явный контроль flush
    )

    @provide
    async def get_db_session(self) -> AsyncGenerator[AsyncSession]:
        """
        Получение сессии базы данных.
        
        Создаёт новую сессию для каждого запроса через context manager.
        Сессия автоматически закрывается при выходе из контекста.
        
        Yields:
            AsyncSession: Асинхронная сессия SQLAlchemy
            
        Example:
            >>> async with get_db_session() as session:
            ...     result = await session.execute(query)
        """
        async with self.session_factory() as session:
            yield session
