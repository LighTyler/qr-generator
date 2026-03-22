"""
Репозиторий для работы с пользователями в базе данных.

Предоставляет интерфейс для CRUD операций с пользователями:
- Создание пользователей
- Получение пользователей по различным критериям
- Обновление данных пользователей
- Управление верификацией email и OTP секретами
"""

from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User, RoleEnum
from schemas.user import UserCreate, UserUpdate, UserCreateConsole


class IUserRepository(Protocol):
    """
    Протокол (интерфейс) репозитория пользователей.
    
    Определяет контракт для работы с пользователями.
    Используется для dependency injection и тестирования.
    
    Methods:
        create: Создание нового пользователя
        get: Получение пользователя по ID
        get_user_by_email_token: Получение пользователя по токену
        get_all: Получение списка пользователей с пагинацией
        update: Обновление данных пользователя
        get_user_by_email: Получение пользователя по email
        set_is_verify_user: Подтверждение email пользователя
        set_otp_secret: Установка секрета для 2FA
        get_otp_secret: Получение секрета 2FA
    """
    
    async def create(
        self,
        user_data: UserCreate | UserCreateConsole,
    ) -> User: ...

    async def get(self, user_id: int) -> User: ...

    async def get_user_by_email_token(self, token: str) -> User | None: ...

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 20,
    ) -> list[User]: ...

    async def update(self, user_data: UserUpdate) -> User: ...

    async def get_user_by_email(self, email: str) -> User | None: ...

    async def set_is_verify_user(self, user: User) -> bool: ...

    async def set_otp_secret(self, user: User, otp_secret: str | None): ...

    async def get_otp_secret(self, user: User) -> str | None: ...


class UserRepository(IUserRepository):
    """
    Реализация репозитория пользователей на SQLAlchemy.
    
    Предоставляет асинхронные методы для работы с таблицей users.
    
    Attributes:
        session (AsyncSession): Асинхронная сессия SQLAlchemy для работы с БД
    """
    
    def __init__(
        self,
        session: AsyncSession,
    ):
        """
        Инициализация репозитория.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
        """
        self.session = session


    async def get(self, user_id: int) -> User | None:
        """
        Получение пользователя по ID.
        
        Args:
            user_id: Идентификатор пользователя
            
        Returns:
            User | None: Объект пользователя или None если не найден
        """
        query = select(User).where(User.id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 20,
    ) -> list[User] | None:
        """
        Получение списка пользователей с пагинацией.
        
        Args:
            offset: Смещение для пагинации (по умолчанию 0)
            limit: Максимальное количество записей (по умолчанию 20)
            
        Returns:
            list[User] | None: Список пользователей или пустой список
        """
        query = select(User).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update(self, user_id: int, user_data: UserUpdate) -> User | None:
        """
        Обновление данных пользователя.
        
        Обновляет только те поля, которые переданы в user_data.
        
        Args:
            user_id: Идентификатор пользователя
            user_data: Данные для обновления (только заполненные поля)
            
        Returns:
            User | None: Обновлённый пользователь или None если не найден
        """
        user = await self.get(user_id)
        if not user:
            return None
        
        # Получаем только те поля, которые были явно установлены
        updated_data = user_data.model_dump(exclude_unset=True)
        
        # Применяем изменения
        for field, value in updated_data.items():
            setattr(user, field, value)
            
        self.session.add(user)
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        """
        Получение пользователя по email адресу.
        
        Используется для аутентификации и проверки уникальности email.
        
        Args:
            email: Email адрес пользователя
            
        Returns:
            User | None: Объект пользователя или None если не найден
        """
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_email_token(self, token: str) -> User | None:
        """
        Получение пользователя по токену.
        
        Используется для верификации email и сброса пароля.
        
        Args:
            token: Токен пользователя (хранится в поле token)
            
        Returns:
            User | None: Объект пользователя или None если токен не найден
        """
        query = select(User).where(User.token == token)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def set_is_verify_user(self, user: User, token: str) -> User:
        """
        Подтверждение email адреса пользователя.
        
        Устанавливает флаг email_verified в True.
        
        Args:
            user: Объект пользователя
            token: Токен подтверждения (для совместимости)
            
        Returns:
            User: Обновлённый объект пользователя
        """
        user.email_verified = True
        self.session.add(user)
        return user

    async def set_otp_secret(self, user: User, otp_secret: str | None):
        """
        Установка или удаление секрета для двухфакторной аутентификации.
        
        Args:
            user: Объект пользователя
            otp_secret: Секретный ключ TOTP или None для удаления 2FA
            
        Returns:
            User: Обновлённый объект пользователя
        """
        user.otp_secret = otp_secret
        self.session.add(user)
        return user

    async def get_otp_secret(self, user: User) -> str | None:
        """
        Получение секрета двухфакторной аутентификации пользователя.
        
        Args:
            user: Объект пользователя
            
        Returns:
            str | None: Секретный ключ TOTP или None если 2FA не настроена
        """
        query = select(User.otp_secret).where(User.id == user.id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
