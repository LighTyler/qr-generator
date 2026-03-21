from fastapi import APIRouter, HTTPException, status
from dishka.integrations.fastapi import FromDishka, DishkaRoute

from schemas.user import UserResponse
from schemas.qr import QRResponse, QRRequest
from services.qr import QRService


router = APIRouter(
    prefix="/qr",
    tags=["QR-code"],
    route_class=DishkaRoute,
)


@router.post("/get-qr", response_model=QRRequest.token)
async def get(
    user: FromDishka[UserResponse.email],
    service: FromDishka[QRService],
    ):
    token = await service.generate_token(user)
    return {"msg": token}

@router.post("/check-qr")
async def check(
    user: QRRequest.token,
    service: FromDishka[QRService],
    ):
    check = await service.check_token(user)
    if check:
        return
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)