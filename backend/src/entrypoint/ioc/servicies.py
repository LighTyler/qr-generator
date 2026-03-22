"""
Провайдер бизнес-сервисов для dependency injection.

Регистрирует сервисы приложения в DI контейнере Dishka.
Все сервисы создаются в scope REQUEST - по одному экземпляру на каждый HTTP запрос.
"""

from dishka import Provider, Scope, provide

from core.uow import UnitOfWork

from repositories.user import IUserRepository
from repositories.qr import QRRepositoryI
from services.user import UserService
from services.qr import QRService


class ServiceProvider(Provider):
    """
    Провайдер бизнес-сервисов.
    
    Создаёт экземпляры сервисов для каждого HTTP запроса.
    Сервисы получают свои зависимости (репозитории, UoW) через DI.
    
    Scope: REQUEST - новый экземпляр на каждый запрос
    """
    scope = Scope.REQUEST

    @provide
    def get_user_service(
        self,
        user_repository: IUserRepository,
    ) -> UserService:
        """
        Создание сервиса пользователей.
        
        Args:
            user_repository: Репозиторий для работы с пользователями
            
        Returns:
            UserService: Экземпляр сервиса пользователей
        """
        return UserService(user_repository)

    @provide
    def get_qr_service(
        self,
        uow: UnitOfWork,
        qr_repository: QRRepositoryI,
    ) -> QRService:
        """
        Создание сервиса QR-токенов.
        
        Args:
            uow: Unit of Work для управления транзакциями
            qr_repository: Репозиторий для работы с QR-токенами
            
        Returns:
            QRService: Экземпляр сервиса QR-токенов
        """
        return QRService(uow, qr_repository)
