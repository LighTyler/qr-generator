from fastapi import WebSocket
from datetime import datetime
import uuid


class ConnectionManager:
    def __init__(self):
        # connection_id -> WebSocket
        self.active_connections: dict[str, WebSocket] = {}
        # user_id -> connection_id (для обратной совместимости)
        self.user_connections: dict[int, str] = {}

    def generate_connection_id(self) -> str:
        """Генерирует уникальный ID соединения."""
        return str(uuid.uuid4())

    async def connect(self, websocket: WebSocket) -> str:
        """Принимает WebSocket соединение и возвращает connection_id."""
        await websocket.accept()
        connection_id = self.generate_connection_id()
        self.active_connections[connection_id] = websocket
        return connection_id

    async def connect_with_user(self, websocket: WebSocket, user_id: int) -> str:
        """Принимает WebSocket соединение с привязкой к user_id.
        
        Возвращает connection_id.
        """
        connection_id = await self.connect(websocket)
        self.user_connections[user_id] = connection_id
        return connection_id

    def disconnect(self, connection_id: str) -> str | None:
        """Отключает соединение по connection_id."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        # Удаляем также из user_connections
        for user_id, conn_id in list(self.user_connections.items()):
            if conn_id == connection_id:
                del self.user_connections[user_id]
                break
        
        return connection_id

    def disconnect_by_user(self, user_id: int) -> str | None:
        """Отключает соединение по user_id (обратная совместимость)."""
        if user_id in self.user_connections:
            connection_id = self.user_connections[user_id]
            return self.disconnect(connection_id)
        return None

    async def disconnect_by_connection_id(self, connection_id: str) -> bool:
        """Принудительно закрывает WebSocket соединение и удаляет его."""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.close(code=1000, reason="Token invalidated")
            except Exception:
                pass  # Соединение уже может быть закрыто
            self.disconnect(connection_id)
            return True
        return False

    async def send_message(self, connection_id: str, message: dict) -> bool:
        """Отправляет сообщение по connection_id."""
        if connection_id in self.active_connections:
            await self.active_connections[connection_id].send_json(message)
            return True
        return False

    async def send_status(self, user_id: int, message: dict) -> bool:
        """Отправляет статус по user_id (обратная совместимость)."""
        if user_id in self.user_connections:
            connection_id = self.user_connections[user_id]
            return await self.send_message(connection_id, message)
        return False

    def get_connection_id_by_user(self, user_id: int) -> str | None:
        """Получает connection_id по user_id."""
        return self.user_connections.get(user_id)


manager = ConnectionManager()
