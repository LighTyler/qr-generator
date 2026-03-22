from fastapi import APIRouter, HTTPException, status
from dishka.integrations.fastapi import FromDishka, DishkaRoute

from schemas.user import UserResponse
from schemas.qr import QRResponse, QRRequest, CheckTokenRequest
from services.qr import QRService


router = APIRouter(
    prefix="/qr",
    tags=["QR-code"],
    route_class=DishkaRoute,
)


@router.post("/get-qr")
async def get(
    user: FromDishka[UserResponse],
    service: FromDishka[QRService],
    ):
    token = await service.generate_token(user)
    return {"msg": token}


@router.post("/check-qr")
async def check(
    user: QRRequest,
    service: FromDishka[QRService],
    ):
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
    """Проверка QR-токена от доверенного сервера.
    Возвращает данные пользователя если токен валиден.
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
