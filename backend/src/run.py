"""
Точка входа FastAPI приложения.

Этот модуль создаёт и настраивает FastAPI приложение:
- Настраивает middleware (CORS)
- Подключает роутеры
- Инициализирует DI контейнер Dishka
- Регистрирует WebSocket endpoint для генерации QR-токенов

Запуск:
    uvicorn run:make_app --factory --host 0.0.0.0 --port 8000
"""

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

# Логгер для модуля
logger = logging.getLogger(__name__)


def make_app(*di_providers: Provider) -> FastAPI:
    """
    Фабрика для создания FastAPI приложения.
    
    Выполняет полную настройку приложения:
    1. Создаёт экземпляр FastAPI
    2. Настраивает CORS middleware
    3. Подключает роутеры
    4. Инициализирует DI контейнер Dishka
    5. Регистрирует WebSocket endpoint
    
    Args:
        *di_providers: Дополнительные провайдеры DI (для тестирования)
        
    Returns:
        FastAPI: Полностью настроенное приложение
        
    Note:
        Функция называется make_app для совместимости с uvicorn --factory
    """
    # Создаём экземпляр FastAPI с lifespan
    app: FastAPI = create_app()

    # Настраиваем middleware (CORS)
    configure_middlewares(app=app)

    # Подключаем роутеры к приложению
    configure_app(app=app, root_router=root_router)

    # Получаем все провайдеры DI
    providers = get_providers()

    # Создаём DI контейнер с провайдерами
    async_container: AsyncContainer = create_async_container(
        [
            *providers,
            *di_providers,
        ]
    )
    
    # Интегрируем Dishka с FastAPI
    setup_dishka(container=async_container, app=app)

    # WebSocket endpoint для генерации QR-токенов
    # Использует ручное получение зависимостей из контейнера
    @app.websocket("/ws/qr-token")
    async def websocket_qr_token(websocket: WebSocket):
        """
        WebSocket endpoint для генерации QR-токенов.
        
        Протокол взаимодействия:
        1. Клиент подключается к /ws/qr-token
        2. Клиент отправляет: {"access_token": "<jwt_token>"}
        3. Сервер проверяет токен через основной сервер (/api/users/me)
        4. Сервер генерирует QR-токен и отправляет:
           {"type": "token", "token": "<qr_token>", "connection_id": "<uuid>"}
        5. При разрыве соединения токен автоматически инвалидируется
        
        Особенности:
        - Токен привязан к WebSocket-соединению через connection_id
        - TTL токена: 5 минут
        - При разрыве соединения токен удаляется из БД
        """
        # Создаём request-scoped контейнер для WebSocket соединения
        async with async_container() as request_container:
            # Получаем зависимости из контейнера
            session = await request_container.get(AsyncSession)
            qr_repository = QRRepository(session)
            uow = UnitOfWork(session)
            
            # Создаём обработчик WebSocket и обрабатываем соединение
            handler = WebSocketHandler(uow, qr_repository)
            await handler.handle_connection(websocket)

    return app
