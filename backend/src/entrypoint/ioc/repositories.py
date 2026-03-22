"""
Провайдер репозиториев для dependency injection.

Регистрирует репозитории и Unit of Work в DI контейнере Dishka.
Все объекты создаются в scope REQUEST - по одному экземпляру на каждый HTTP запрос.
"""

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession

from core.uow import UnitOfWork
from repositories import (
    IUserRepository,
    UserRepository,
)
from repositories.qr import QRRepositoryI, QRRepository


class RepositoryProvider(Provider):
    """
    Провайдер репозиториев для работы с данными.
    
    Создаёт экземпляры репозиториев и Unit of Work для каждого HTTP запроса.
    Все репозитории используют одну и ту же сессию БД в рамках запроса.
    
    Scope: REQUEST - новый экземпляр на каждый запрос
    """
    scope = Scope.REQUEST

    @provide
    def get_user_repository(self, session: AsyncSession) -> IUserRepository:
        """
        Создание репозитория пользователей.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            
        Returns:
            IUserRepository: Экземпляр репозитория пользователей
        """
        return UserRepository(session)

    @provide
    def get_qr_repository(self, session: AsyncSession) -> QRRepositoryI:
        """
        Создание репозитория QR-токенов.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            
        Returns:
            QRRepositoryI: Экземпляр репозитория QR-токенов
        """
        return QRRepository(session)

    @provide
    def get_unit_of_work(self, session: AsyncSession) -> UnitOfWork:
        """
        Создание Unit of Work для управления транзакциями.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            
        Returns:
            UnitOfWork: Экземпляр Unit of Work
        """
        return UnitOfWork(session)
