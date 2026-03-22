"""
WebSocket роутер для генерации QR-токенов.

Обеспечивает WebSocket-соединение между клиентом (фронтендом) и сервером
для генерации QR-токенов с автоматической инвалидацией при разрыве соединения.

Жизненный цикл соединения:
1. Клиент подключается по WebSocket
2. Отправляет access_token для авторизации
3. Сервер верифицирует токен через основной сервер
4. Генерирует QR-токен, привязанный к connection_id
5. Отправляет токен клиенту
6. Поддерживает keepalive (ping/pong)
7. При разрыве - токен автоматически инвалидируется
"""

import asyncio
import logging
from fastapi import WebSocket, WebSocketDisconnect, status
from httpx import AsyncClient, HTTPError

from entrypoint.config import config
from schemas.qr import WSAuthMessage
from schemas.user import UserResponse
from services.ws_manager import manager as ws_manager
from services.qr import QRService
from core.uow import UnitOfWork
from repositories.qr import QRRepository

# Логгер для модуля
logger = logging.getLogger(__name__)


class WebSocketHandler:
    """
    Обработчик WebSocket для генерации QR-токенов с автоматической инвалидацией.
    
    Отвечает за полный жизненный цикл WebSocket-соединения:
    - Подключение и регистрация в менеджере
    - Авторизация через основной сервер
    - Генерация QR-токена с привязкой к connection_id
    - Поддержание соединения (keepalive)
    - Гарантированная инвалидация токена при разрыве
    
    Токен привязывается к WebSocket-соединению через connection_id.
    При разрыве соединения токен автоматически удаляется из БД.
    
    Attributes:
        uow (UnitOfWork): Unit of Work для управления транзакциями
        qr_repository (QRRepository): Репозиторий для работы с QR-токенами
        qr_service (QRService): Сервис для бизнес-логики QR-токенов
    """
    
    def __init__(self, uow: UnitOfWork, qr_repository: QRRepository):
        """
        Инициализация обработчика.
        
        Args:
            uow: Unit of Work для управления транзакциями
            qr_repository: Репозиторий для работы с QR-токенами
        """
        self.uow = uow
        self.qr_repository = qr_repository
        self.qr_service = QRService(uow, qr_repository)

    async def handle_connection(self, websocket: WebSocket):
        """
        Обработка WebSocket-соединения от подключения до закрытия.
        
        Жизненный цикл:
        1. Подключение -> получение connection_id
        2. Авторизация -> проверка access_token
        3. Генерация токена -> отправка клиенту
        4. Keepalive -> ожидание ping/pong
        5. Инвалидация -> очистка при разрыве (finally)
        
        Args:
            websocket: Объект WebSocket-соединения FastAPI
        """
        connection_id = None
        
        try:
            # Регистрируем соединение в менеджере
            connection_id = await ws_manager.connect(websocket)
            logger.info(f"WebSocket connected: {connection_id}")
            
            # Ожидаем авторизационное сообщение (таймаут 30 сек)
            auth_data = await asyncio_wait_for_message(websocket, timeout=30)
            if not auth_data:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Auth timeout")
                return
            
            # Парсим авторизационное сообщение
            try:
                auth_message = WSAuthMessage(**auth_data)
            except Exception as e:
                logger.warning(f"Invalid auth message: {e}")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid auth format")
                return
            
            # Верификация access_token через основной сервер
            user_info = await self.verify_user_on_main_server(auth_message.access_token)
            if not user_info:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Unauthorized")
                return
            
            # Извлекаем данные пользователя
            user_id = user_info.get("id")
            username = user_info.get("username")
            email = user_info.get("email")
            
            user = UserResponse(id=user_id, username=username, email=email)
            
            # Генерируем QR-токен с привязкой к connection_id
            qr_token = await self.qr_service.generate_token(user, connection_id)
            
            # Отправляем токен клиенту
            await ws_manager.send_message(connection_id, {
                "type": "token",
                "token": qr_token,
                "connection_id": connection_id,
            })
            
            logger.info(f"QR token generated for user {user_id}, connection {connection_id}")
            
            # Keepalive: держим соединение открытым, отвечаем на ping
            while True:
                try:
                    data = await websocket.receive_json()
                    if data.get("type") == "ping":
                        await ws_manager.send_message(connection_id, {"type": "pong"})
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.debug(f"WebSocket receive error: {e}")
                    break
                    
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {connection_id}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            # Гарантированная инвалидация токена при любом исходе
            if connection_id:
                ws_manager.disconnect(connection_id)
                await self.qr_service.invalidate_by_connection_id(connection_id)
                logger.info(f"Token invalidated for connection {connection_id}")

    async def verify_user_on_main_server(self, access_token: str) -> dict | None:
        """
        Проверка access_token через API основного сервера.
        
        Отправляет запрос к /api/users/me для получения информации о пользователе.
        
        Args:
            access_token: JWT access токен пользователя
            
        Returns:
            dict | None: Данные пользователя или None если токен невалиден
        """
        main_server_url = config.service.URL
        
        try:
            async with AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{main_server_url}/api/users/me",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if response.status_code == 200:
                    return response.json()
                logger.warning(f"User verification failed: {response.status_code}")
                return None
                    
        except HTTPError as e:
            logger.error(f"Error verifying user on main server: {e}")
            return None


async def asyncio_wait_for_message(websocket: WebSocket, timeout: int = 30) -> dict | None:
    """
    Ожидание JSON сообщения от WebSocket с таймаутом.
    
    Утилитарная функция для ожидания первого сообщения от клиента.
    Используется для ожидания авторизационного сообщения.
    
    Args:
        websocket: Объект WebSocket-соединения
        timeout: Таймаут ожидания в секундах (по умолчанию 30)
        
    Returns:
        dict | None: Распарсенный JSON или None при таймауте/ошибке
    """
    try:
        data = await asyncio.wait_for(websocket.receive_json(), timeout=timeout)
        return data
    except asyncio.TimeoutError:
        return None
    except Exception as e:
        logger.debug(f"Error receiving message: {e}")
        return None
