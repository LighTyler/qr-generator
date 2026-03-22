from datetime import datetime, timedelta

from schemas.qr import QRRequest, QRResponse
from schemas.user import UserResponse
from utils.utils import generate_token, check, decrypt_public
from repositories.qr import QRRepositoryI
from core.uow import UnitOfWork
from services.ws_manager import manager as ws_manager


class QRService:
    def __init__(
        self,
        uow: UnitOfWork,
        qr_repository: QRRepositoryI,
    ):
        self.uow = uow
        self.qr_repository = qr_repository

    async def generate_token(self, user: UserResponse, connection_id: str | None = None) -> str:
        """Генерация QR-токена для пользователя.
        
        Args:
            user: Данные пользователя
            connection_id: ID WebSocket соединения (опционально)
        """
        user_dict = user.model_dump()
        salt, token = generate_token(**user_dict)
        qr_resp = QRResponse(user=user, salt=salt, connection_id=connection_id)
        async with self.uow:
            await self.qr_repository.update(qr_resp)

        return token

    async def bind_connection(self, user_id: int, connection_id: str) -> bool:
        """Привязать connection_id к существующему токену."""
        async with self.uow:
            return await self.qr_repository.update_connection_id(user_id, connection_id)

    async def check_token(self, qr_request: QRRequest) -> bool:
        """Проверка QR-токена (для обратной совместимости)."""
        user_rep = await self.qr_repository.get(qr_request)
        if not user_rep:
            return False
        
        # Проверяем время жизни токена
        time_valid = datetime.now() < (user_rep.timestamp + timedelta(minutes=5))
        if not time_valid:
            return False
        
        # Проверяем токен
        token_valid = check(
            username=user_rep.username,
            id=user_rep.user_id,
            email=user_rep.email,
            recieved_token=qr_request.token,
            salt=user_rep.salt,
        )
        
        if token_valid:
            # Удаляем запись после успешной проверки
            async with self.uow:
                await self.qr_repository.delete(user_rep.user_id)
        
        return token_valid and time_valid

    async def verify_token(self, token: str) -> dict | None:
        """Проверка токена от доверенного сервера.
        
        Возвращает данные пользователя если токен валиден.
        При успешной проверке разрывает WebSocket соединение.
        """
        try:
            # Разбираем токен на public и private части
            parts = token.split(".")
            if len(parts) < 2:
                return None
            
            public_part = parts[0]
            # Расшифровываем public часть чтобы получить id и username
            user_id, username = decrypt_public(public_part)
            user_id = int(user_id)
            
            # Получаем запись из БД по user_id
            user_rep = await self.qr_repository.get_by_user_id(user_id)
            
            if not user_rep:
                return None
            
            # Проверяем время жизни токена
            time_valid = datetime.now() < (user_rep.timestamp + timedelta(minutes=5))
            if not time_valid:
                return None
            
            # Сохраняем connection_id до удаления
            connection_id = user_rep.connection_id
            
            # Удаляем запись после успешной проверки
            async with self.uow:
                await self.qr_repository.delete(user_id)
            
            # Если есть активное WebSocket соединение - разрываем его
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
        """Инвалидация токена при разрыве WebSocket соединения."""
        async with self.uow:
            return await self.qr_repository.delete_by_connection_id(connection_id)
