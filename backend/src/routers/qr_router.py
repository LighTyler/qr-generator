"""
Роутер для работы с QR-кодами.

Предоставляет REST API endpoints для:
- Генерации QR-токена (/get-qr)
- Проверки QR-токена мобильным приложением (/check-qr)
- Проверки токена доверенным сервером (/check-token)

Все endpoints используют Dishka для dependency injection.
"""

from fastapi import APIRouter, HTTPException, status
from dishka.integrations.fastapi import FromDishka, DishkaRoute

from schemas.user import UserResponse
from schemas.qr import QRResponse, QRRequest, CheckTokenRequest
from services.qr import QRService


# Создаём роутер с префиксом /qr и использованием DishkaRoute для DI
router = APIRouter(
    prefix="/qr",
    tags=["QR-code"],
    route_class=DishkaRoute,  # Включает автоматический DI через Dishka
)


@router.post("/get-qr")
async def get(
    user: FromDishka[UserResponse],
    service: FromDishka[QRService],
    ):
    """
    Генерация QR-токена для авторизации.
    
    Принимает данные пользователя через DI (из JWT токена).
    Возвращает сгенерированный QR-токен.
    
    Returns:
        dict: {"msg": "<qr_token>"} - токен для отображения в QR-коде
    """
    token = await service.generate_token(user)
    return {"msg": token}


@router.post("/check-qr")
async def check(
    user: QRRequest,
    service: FromDishka[QRService],
    ):
    """
    Проверка QR-токена (используется мобильным приложением).
    
    Мобильное приложение сканирует QR-код и отправляет токен на проверку.
    При успешной проверке токен удаляется (одноразовый).
    
    Args:
        user: QRRequest с токеном из QR-кода
        
    Returns:
        dict: {"status": "ok"} если токен валиден
        
    Raises:
        HTTPException: 401 UNAUTHORIZED если токен невалиден или истёк
    """
    result = await service.check_token(user)
    if result:
        return {"status": "ok"}
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


@router.post("/check-token")
async def check_token(
    request: CheckTokenRequest,
    service: FromDishka[QRService],
    ):
    """
        Проверка QR-токена от доверенного сервера.
        
        Используется основным сервером для проверки токена после сканирования QR.
        При успехе:
        1. Возвращает данные пользователя
        2. Удаляет токен из БД
        3. Разрывает WebSocket-соединение (инвалидация)
        
        Args:
            request: CheckTokenRequest с токеном для проверки
            
        Returns:
            dict: Данные пользователя если токен валиден:
                  {"valid": True, "user_id": int, "username": str, "email": str}
                  
        Raises:
            HTTPException: 401 UNAUTHORIZED если токен невалиден или истёк
        """
    result = await service.verify_token(request.token)
    if result:
        return {
            "valid": True,
            "user_id": result["user_id"],
            "username": result["username"],
            "email": result["email"],
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
