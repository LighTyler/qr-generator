"""
Сервис для работы с пользователями.

Отвечает за бизнес-логику работы с данными пользователей.
Работает через репозиторий для доступа к базе данных.
"""

from schemas.user import UserResponse
from repositories.user import UserRepository


class UserService:
    """
    Сервис для работы с пользователями.
    
    Предоставляет методы для получения данных пользователей.
    Работает через репозиторий для разделения бизнес-логики и доступа к данным.
    
    Attributes:
        user_repository (UserRepository): Репозиторий для работы с пользователями в БД
    """
    
    def __init__(self, user_repository: UserRepository):
        """
        Инициализация сервиса.
        
        Args:
            user_repository: Репозиторий для работы с пользователями
        """
        self.user_repository = user_repository

    async def get_user_by_id(self, user_id: int) -> UserResponse | None:
        """
        Получение пользователя по ID.
        
        Args:
            user_id: Идентификатор пользователя
            
        Returns:
            UserResponse | None: DTO с данными пользователя или None если не найден
        """
        user = await self.user_repository.get(user_id)
        if not user:
            return None
        
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            role=user.role,
        )
