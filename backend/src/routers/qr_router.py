from fastapi import APIRouter, HTTPException, status
from dishka.integrations.fastapi import FromDishka, DishkaRoute

from schemas.user import UserResponse
from schemas.qr import QRResponse, QRRequest
from services.qr import QRService
from starlette.status import HTTP_200_OK


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

@router.post("/check-qr", response_model=HTTP_200_OK)
async def check(
    user: QRRequest,
    service: FromDishka[QRService],
    ):
    check = await service.check_token(user)
    if check:
        return
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)