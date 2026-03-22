import logging
from dishka import AsyncContainer, Provider
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from entrypoint.ioc.registry import get_providers
from entrypoint.setup import (
    configure_app,
    configure_middlewares,
    create_app,
    create_async_container,
)
from routers import root_router
from routers.ws_router import WebSocketHandler
from core.uow import UnitOfWork
from repositories.qr import QRRepository

logger = logging.getLogger(__name__)


def make_app(*di_providers: Provider) -> FastAPI:
    app: FastAPI = create_app()

    configure_middlewares(app=app)

    configure_app(app=app, root_router=root_router)

    providers = get_providers()

    async_container: AsyncContainer = create_async_container(
        [
            *providers,
            *di_providers,
        ]
    )
    setup_dishka(container=async_container, app=app)

    # WebSocket endpoint с ручным получением зависимостей из контейнера
    @app.websocket("/ws/qr-token")
    async def websocket_qr_token(websocket: WebSocket):
        """WebSocket endpoint для генерации QR-токенов.
        
        Протокол:
        1. Клиент подключается
        2. Клиент отправляет {"access_token": "..."}
        3. Сервер проверяет токен через основной сервер
        4. Сервер генерирует QR-токен и отправляет {"type": "token", "token": "...", "connection_id": "..."}
        5. При разрыве соединения токен инвалидируется
        """
        async with async_container() as request_container:
            session = await request_container.get(AsyncSession)
            qr_repository = QRRepository(session)
            uow = UnitOfWork(session)
            
            handler = WebSocketHandler(uow, qr_repository)
            await handler.handle_connection(websocket)

    return app
