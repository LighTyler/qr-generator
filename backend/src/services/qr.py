"""
Сервис для работы с QR-токенами.

Отвечает за бизнес-логику генерации, проверки и инвалидации QR-токенов.
Токены привязываются к WebSocket-соединениям для обеспечения мгновенной инвалидации.
"""

from datetime import datetime, timedelta

from schemas.qr import QRRequest, QRResponse
from schemas.user import UserResponse
from utils.utils import generate_token, check, decrypt_public
from repositories.qr import QRRepositoryI
from core.uow import UnitOfWork
from services.ws_manager import manager as ws_manager


class QRService:
    """
    Сервис QR-токенов с поддержкой WebSocket-инвалидации.
    
    Основные функции:
    - Генерация QR-токенов для авторизации
    - Проверка токенов от мобильного приложения
    - Верификация токенов от доверенных серверов
    - Инвалидация токенов при разрыве WebSocket-соединения
    
    Токен привязывается к WebSocket-соединению через connection_id.
    При разрыве соединения токен автоматически удаляется из БД.
    
    Attributes:
        uow (UnitOfWork): Unit of Work для управления транзакциями
        qr_repository (QRRepositoryI): Репозиторий для работы с QR-токенами
    """
    
    def __init__(self, uow: UnitOfWork, qr_repository: QRRepositoryI):
        """
        Инициализация сервиса.
        
        Args:
            uow: Unit of Work для управления транзакциями
            qr_repository: Репозиторий для работы с QR-токенами в БД
        """
        self.uow = uow
        self.qr_repository = qr_repository

    async def generate_token(self, user: UserResponse, connection_id: str | None = None) -> str:
        """
        Генерация QR-токена с опциональной привязкой к WebSocket.
        
        Создаёт токен, сохраняет его в БД и возвращает строку для QR-кода.
        
        Args:
            user: Данные пользователя для которого генерируется токен
            connection_id: ID WebSocket-соединения для привязки (опционально)
            
        Returns:
            str: Сгенерированный токен в формате "public_part.private_part"
        """
        user_dict = user.model_dump()
        salt, token = generate_token(**user_dict)
        qr_resp = QRResponse(user=user, salt=salt, connection_id=connection_id)
        async with self.uow:
            await self.qr_repository.update(qr_resp)
        return token

    async def bind_connection(self, user_id: int, connection_id: str) -> bool:
        """
        Привязка connection_id к существующему токену.
        
        Используется когда WebSocket-соединение устанавливается после генерации токена.
        
        Args:
            user_id: ID пользователя
            connection_id: ID WebSocket-соединения для привязки
            
        Returns:
            bool: True если привязка успешна, False если токен не найден
        """
        async with self.uow:
            return await self.qr_repository.update_connection_id(user_id, connection_id)

    async def check_token(self, qr_request: QRRequest) -> bool:
        """
        Проверка токена (legacy метод, используется мобильным приложением).
        
        Проверяет:
        1. Существование токена в БД
        2. TTL токена (5 минут)
        3. Валидность криптографической подписи
        
        При успешной проверке токен удаляется из БД.
        
        Args:
            qr_request: Запрос с токеном для проверки
            
        Returns:
            bool: True если токен валиден, False иначе
        """
        user_rep = await self.qr_repository.get(qr_request)
        if not user_rep:
            return False
        
        # TTL: 5 минут с момента создания
        time_valid = datetime.now() < (user_rep.timestamp + timedelta(minutes=5))
        if not time_valid:
            return False
        
        # Криптографическая проверка токена
        token_valid = check(
            username=user_rep.username,
            id=user_rep.user_id,
            email=user_rep.email,
            recieved_token=qr_request.token,
            salt=user_rep.salt,
        )
        
        # Удаляем токен при успешной проверке
        if token_valid:
            async with self.uow:
                await self.qr_repository.delete(user_rep.user_id)
        
        return token_valid and time_valid

    async def verify_token(self, token: str) -> dict | None:
        """
        Верификация токена от доверенного сервера (/check-token).
        
        При успехе:
        1. Возвращает данные пользователя
        2. Удаляет токен из БД
        3. Разрывает WebSocket-соединение
        
        Это гарантирует мгновенную инвалидацию токена после использования.
        
        Args:
            token: Токен для верификации в формате "public_part.private_part"
            
        Returns:
            dict | None: Словарь с данными пользователя {'user_id', 'username', 'email', 'valid'}
                         или None если токен невалиден
        """
        try:
            parts = token.split(".")
            if len(parts) < 2:
                return None
            
            # Извлекаем user_id из public части токена
            public_part = parts[0]
            user_id, username = decrypt_public(public_part)
            user_id = int(user_id)
            
            user_rep = await self.qr_repository.get_by_user_id(user_id)
            if not user_rep:
                return None
            
            # Проверяем TTL (5 минут)
            time_valid = datetime.now() < (user_rep.timestamp + timedelta(minutes=5))
            if not time_valid:
                return None
            
            connection_id = user_rep.connection_id
            
            # Удаляем токен из БД (токен одноразовый)
            async with self.uow:
                await self.qr_repository.delete(user_id)
            
            # Разрываем WebSocket -> токен полностью инвалидирован
            if connection_id:
                await ws_manager.disconnect_by_connection_id(connection_id)
            
            return {
                "user_id": user_id,
                "username": username,
                "email": user_rep.email,
                "valid": True
            }
        except Exception:
            return None

    async def invalidate_by_connection_id(self, connection_id: str) -> bool:
        """
        Удаление токена при разрыве WebSocket-соединения.
        
        Вызывается из finally блока обработчика WebSocket для гарантии
        удаления токена при любом исходе соединения.
        
        Args:
            connection_id: ID WebSocket-соединения
            
        Returns:
            bool: True если токен был удалён, False если токен не найден
        """
        async with self.uow:
            return await self.qr_repository.delete_by_connection_id(connection_id)
