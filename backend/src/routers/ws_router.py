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

    def __init__(self, uow: UnitOfWork, qr_repository: QRRepository):

        self.uow = uow
        self.qr_repository = qr_repository
        self.qr_service = QRService(uow, qr_repository)

    async def handle_connection(self, websocket: WebSocket):

        connection_id = None

        try:
            connection_id = await ws_manager.connect(websocket)
            logger.info(f"WebSocket connected: {connection_id}")

            auth_data = await asyncio_wait_for_message(websocket, timeout=30)
            if not auth_data:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Auth timeout")
                return

            try:
                auth_message = WSAuthMessage(**auth_data)
            except Exception as e:
                logger.warning(f"Invalid auth message: {e}")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid auth format")
                return

            user_info = await self.verify_user_on_main_server(auth_message.access_token)
            if not user_info:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Unauthorized")
                return

            user_id = user_info.get("id")
            username = user_info.get("username")
            email = user_info.get("email")

            user = UserResponse(id=user_id, username=username, email=email)

            qr_token = await self.qr_service.generate_token(user, connection_id)

            await ws_manager.send_message(connection_id, {
                "type": "token",
                "token": qr_token,
                "connection_id": connection_id,
            })

            logger.info(f"QR token generated for user {user_id}, connection {connection_id}")

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
            if connection_id:
                ws_manager.disconnect(connection_id)
                await self.qr_service.invalidate_by_connection_id(connection_id)
                logger.info(f"Token invalidated for connection {connection_id}")

    async def verify_user_on_main_server(self, access_token: str) -> dict | None:
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
    try:
        data = await asyncio.wait_for(websocket.receive_json(), timeout=timeout)
        return data
    except asyncio.TimeoutError:
        return None
    except Exception as e:
        logger.debug(f"Error receiving message: {e}")
        return None
