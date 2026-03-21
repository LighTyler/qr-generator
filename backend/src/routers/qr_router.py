import json
from fastapi import FastApi, APIRouter, HTTPException, status, WebSocket, WebSocketDisconnect
from dishka.integrations.fastapi import FromDishka, DishkaRoute

from repositories import IUserRepository
from repositories.qr import QRRepositoryI
from schemas.user import UserResponse
from schemas.qr import QRResponse, QRRequest
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
    check = await service.check_token(user)
    if check:
        return
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    service: FromDishka[QRService],
    user_repository: FromDishka[IUserRepository],
    qr_repository: FromDishka[QRRepositoryI],
):
    await websocket.accept()
    user_email = None  # Сохраняем email для очистки при отключении
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                # Парсим JSON из входящих данных
                payload = json.loads(data)
                uuid = payload.get("uuid")
                
                if uuid:
                    # Ищем пользователя по UUID токену
                    user = await user_repository.get_user_by_email_token(uuid)
                    
                    if user:
                        # Сохраняем email для очистки при отключении
                        user_email = user.email
                        
                        # Генерируем токен через сервис
                        user_response = UserResponse(
                            id=user.id,
                            username=user.username,
                            email=user.email
                        )
                        token = await service.generate_token(user_response)
                        await websocket.send_json({
                            "token": token,
                            "user_id": user.id
                        })
                    else:
                        await websocket.send_json({
                            "error": "User not found"
                        })
                else:
                    await websocket.send_json({
                        "error": "UUID is required"
                    })
            except json.JSONDecodeError:
                await websocket.send_json({
                    "error": "Invalid JSON format"
                })
    except WebSocketDisconnect:
        # При отключении клиента удаляем QR запись
        if user_email:
            async with service.uow:
                await qr_repository.delete_by_email(user_email)
    except Exception as e:
        # При ошибке также удаляем QR запись
        if user_email:
            async with service.uow:
                await qr_repository.delete_by_email(user_email)
        await websocket.send_json({
            "error": f"Internal server error: {str(e)}"
        })
