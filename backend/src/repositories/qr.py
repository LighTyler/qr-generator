"""
Репозиторий для работы с QR-токенами в базе данных.

Предоставляет интерфейс для CRUD операций с QR-токенами.
Токены привязаны к пользователям через user_id и к WebSocket через connection_id.
"""

from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.qr import QRRequest, QRResponse
from models.qr import QR


class QRRepositoryI(Protocol):
    """
    Протокол (интерфейс) репозитория QR-токенов.
    
    Определяет контракт для работы с QR-токенами.
    Используется для dependency injection и тестирования.
    
    Methods:
        create: Создание нового QR-токена
        get: Получение токена по зашифрованному токену из запроса
        get_by_user_id: Получение токена по ID пользователя
        get_by_connection_id: Получение токена по ID WebSocket-соединения
        update: Создание или обновление токена (upsert)
        update_connection_id: Обновление только connection_id
        delete: Удаление токена по user_id
        delete_by_connection_id: Удаление токена по connection_id
    """
    
    async def create(self, qrdata: QRResponse) -> QR: ...
    async def get(self, qrdata: QRRequest) -> QR | None: ...
    async def get_by_user_id(self, user_id: int) -> QR | None: ...
    async def get_by_connection_id(self, connection_id: str) -> QR | None: ...
    async def update(self, qrdata: QRResponse) -> QR | None: ...
    async def update_connection_id(self, user_id: int, connection_id: str | None) -> bool: ...
    async def delete(self, user_id: int) -> bool: ...
    async def delete_by_connection_id(self, connection_id: str) -> bool: ...


class QRRepository(QRRepositoryI):
    """
    Реализация репозитория QR-токенов на SQLAlchemy.
    
    Токены хранятся по user_id (primary) и connection_id (для инвалидации по WebSocket).
    
    Attributes:
        session (AsyncSession): Асинхронная сессия SQLAlchemy для работы с БД
    """
    
    def __init__(self, session: AsyncSession):
        """
        Инициализация репозитория.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
        """
        self.session = session

    async def create(self, qrdata: QRResponse) -> QR:
        """
        Создание нового QR-токена в базе данных.
        
        Args:
            qrdata: Данные для создания токена (информация о пользователе, salt, connection_id)
            
        Returns:
            QR: Созданный объект токена с заполненными полями
        """
        qr = QR(
            user_id=qrdata.user.id,
            username=qrdata.user.username,
            email=qrdata.user.email,
            salt=qrdata.salt,
            connection_id=qrdata.connection_id,
        )
        self.session.add(qr)
        await self.session.flush()
        await self.session.refresh(qr)
        return qr
    
    async def get(self, qrdata: QRRequest) -> QR | None:
        """
        Получение токена по зашифрованному токену из запроса.
        
        Расшифровывает публичную часть токена для получения user_id.
        
        Args:
            qrdata: Запрос с зашифрованным токеном
            
        Returns:
            QR | None: Найденный токен или None если токен невалиден
        """
        from utils.utils import decrypt_public
        
        parts = qrdata.token.split(".")
        if len(parts) < 2:
            return None
        
        try:
            user_id, _ = decrypt_public(parts[0])
            return await self.get_by_user_id(int(user_id))
        except Exception:
            return None

    async def get_by_user_id(self, user_id: int) -> QR | None:
        """
        Получение токена по ID пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            QR | None: Токен пользователя или None если не найден
        """
        query = select(QR).where(QR.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_connection_id(self, connection_id: str) -> QR | None:
        """
        Получение токена по ID WebSocket-соединения.
        
        Используется для поиска токена при разрыве WebSocket соединения.
        
        Args:
            connection_id: ID WebSocket-соединения
            
        Returns:
            QR | None: Токен или None если не найден
        """
        query = select(QR).where(QR.connection_id == connection_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update(self, qrdata: QRResponse) -> QR | None:
        """
        Upsert операция: создаёт или обновляет запись токена.
        
        Если токен для пользователя уже существует - обновляет его.
        Если не существует - создаёт новый.
        
        Args:
            qrdata: Данные токена для создания/обновления
            
        Returns:
            QR | None: Созданный или обновлённый токен
        """
        qr = await self.get_by_user_id(qrdata.user.id)
        if not qr:
            return await self.create(qrdata)
        
        # Обновляем существующий токен
        qr.username = qrdata.user.username
        qr.email = qrdata.user.email
        qr.salt = qrdata.salt
        if qrdata.connection_id is not None:
            qr.connection_id = qrdata.connection_id
        
        await self.session.flush()
        await self.session.refresh(qr)
        return qr

    async def update_connection_id(self, user_id: int, connection_id: str | None) -> bool:
        """
        Обновление только connection_id токена.
        
        Используется для привязки/отвязки WebSocket-соединения к токену.
        
        Args:
            user_id: ID пользователя
            connection_id: Новый ID соединения или None для отвязки
            
        Returns:
            bool: True если обновление прошло успешно, False если токен не найден
        """
        qr = await self.get_by_user_id(user_id)
        if not qr:
            return False
        
        qr.connection_id = connection_id
        await self.session.flush()
        return True

    async def delete(self, user_id: int) -> bool:
        """
        Удаление токена по user_id.
        
        Вызывается при успешной верификации QR-кода.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            bool: True если удаление прошло успешно, False если токен не найден
        """
        qr = await self.get_by_user_id(user_id)
        if not qr:
            return False
        
        await self.session.delete(qr)
        await self.session.flush()
        return True

    async def delete_by_connection_id(self, connection_id: str) -> bool:
        """
        Удаление токена по connection_id.
        
        Вызывается при разрыве WebSocket-соединения для инвалидации токена.
        
        Args:
            connection_id: ID WebSocket-соединения
            
        Returns:
            bool: True если удаление прошло успешно, False если токен не найден
        """
        qr = await self.get_by_connection_id(connection_id)
        if not qr:
            return False
        
        await self.session.delete(qr)
        await self.session.flush()
        return True
