"""Схемы Pydantic для QR-токенов.

Содержит модели для:
- Генерации токена (QRResponse)
- Проверки токена (QRRequest, CheckTokenRequest/Response)
- Авторизации через WebSocket (WSAuthMessage)
"""

from pydantic import BaseModel

from schemas.user import UserResponse


class QRBase(BaseModel):
    """Базовая схема с информацией о пользователе."""
    user: UserResponse


class QRResponse(QRBase):
    """Ответ при генерации QR-токена."""
    salt: str
    connection_id: str | None = None


class QRRequest(BaseModel):
    """Запрос для проверки QR-токена (mobile -> server)."""
    token: str


class CheckTokenRequest(BaseModel):
    """Запрос для REST API проверки токена."""
    token: str


class CheckTokenResponse(BaseModel):
    """Ответ REST API /check-token.
    
    При успешной проверке разрывает WebSocket-соединение,
    что автоматически инвалидирует токен.
    """
    valid: bool
    user_id: int | None = None
    username: str | None = None
    email: str | None = None


class WSAuthMessage(BaseModel):
    """Первое сообщение WebSocket для авторизации.
    
    Содержит access_token от основного сервера.
    Валидируется через /api/users/me.
    """
    access_token: str
