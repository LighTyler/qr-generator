"""
Менеджер WebSocket-соединений.

Отвечает за управление WebSocket-соединениями в приложении:
- Отслеживание активных соединений
- Принудительное закрытие соединений при инвалидации токена
- Отправка сообщений клиентам
- Связывание соединений с пользователями
"""

from fastapi import WebSocket
import uuid


class ConnectionManager:
    """
    Менеджер WebSocket-соединений с поддержкой connection_id.
    
    Каждому соединению присваивается уникальный connection_id (UUID).
    Соединения могут быть опционально привязаны к user_id.
    
    Используется для:
    - Отслеживания активных соединений
    - Принудительного закрытия соединений при инвалидации токена
    - Отправки сообщений конкретным клиентам
    
    Attributes:
        active_connections (dict[str, WebSocket]): Маппинг connection_id -> WebSocket
        user_connections (dict[int, str]): Маппинг user_id -> connection_id (опционально)
    
    Example:
        >>> manager = ConnectionManager()
        >>> connection_id = await manager.connect(websocket)
        >>> await manager.send_message(connection_id, {"status": "ok"})
        >>> await manager.disconnect_by_connection_id(connection_id)
    """
    
    def __init__(self):
        """Инициализация менеджера с пустыми словарями соединений."""
        # connection_id -> WebSocket
        self.active_connections: dict[str, WebSocket] = {}
        # user_id -> connection_id (опционально, для связи с пользователем)
        self.user_connections: dict[int, str] = {}

    def generate_connection_id(self) -> str:
        """
        Генерация уникального ID для соединения.
        
        Returns:
            str: UUID в строковом представлении
        """
        return str(uuid.uuid4())

    async def connect(self, websocket: WebSocket) -> str:
        """
        Принятие нового WebSocket-соединения.
        
        Принимает соединение, генерирует уникальный connection_id
        и регистрирует соединение в менеджере.
        
        Args:
            websocket: Объект WebSocket-соединения FastAPI
            
        Returns:
            str: Уникальный connection_id для этого соединения
        """
        await websocket.accept()
        connection_id = self.generate_connection_id()
        self.active_connections[connection_id] = websocket
        return connection_id

    async def connect_with_user(self, websocket: WebSocket, user_id: int) -> str:
        """
        Принятие соединения с привязкой к user_id.
        
        Удобный метод для случаев, когда нужно отслеживать
        соединения по ID пользователя.
        
        Args:
            websocket: Объект WebSocket-соединения FastAPI
            user_id: ID пользователя для привязки
            
        Returns:
            str: Уникальный connection_id для этого соединения
        """
        connection_id = await self.connect(websocket)
        self.user_connections[user_id] = connection_id
        return connection_id

    def disconnect(self, connection_id: str) -> str | None:
        """
        Удаление соединения из реестра (без закрытия WebSocket).
        
        Вызывается когда соединение уже закрыто или будет закрыто извне.
        Удаляет связь connection_id -> WebSocket и user_id -> connection_id.
        
        Args:
            connection_id: ID соединения для удаления
            
        Returns:
            str | None: Удалённый connection_id или None если не найден
        """
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        # Очистка связи user_id -> connection_id
        for user_id, conn_id in list(self.user_connections.items()):
            if conn_id == connection_id:
                del self.user_connections[user_id]
                break
        
        return connection_id

    def disconnect_by_user(self, user_id: int) -> str | None:
        """
        Удаление соединения по user_id.
        
        Находит connection_id по user_id и удаляет соединение.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            str | None: Удалённый connection_id или None если не найден
        """
        if user_id in self.user_connections:
            return self.disconnect(self.user_connections[user_id])
        return None

    async def disconnect_by_connection_id(self, connection_id: str) -> bool:
        """
        Принудительное закрытие WebSocket-соединения.
        
        Используется при /check-token для мгновенной инвалидации токена.
        Закрывает WebSocket с кодом 1000 (нормальное закрытие).
        
        Args:
            connection_id: ID соединения для закрытия
            
        Returns:
            bool: True если соединение было закрыто, False если не найдено
        """
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.close(code=1000, reason="Token invalidated")
            except Exception:
                pass  # Соединение уже закрыто клиентом
            self.disconnect(connection_id)
            return True
        return False

    async def send_message(self, connection_id: str, message: dict) -> bool:
        """
        Отправка JSON сообщения по connection_id.
        
        Args:
            connection_id: ID соединения-получателя
            message: Словарь с данными для отправки (будет сериализован в JSON)
            
        Returns:
            bool: True если сообщение отправлено, False если соединение не найдено
        """
        if connection_id in self.active_connections:
            await self.active_connections[connection_id].send_json(message)
            return True
        return False

    async def send_status(self, user_id: int, message: dict) -> bool:
        """
        Отправка сообщения по user_id.
        
        Находит connection_id по user_id и отправляет сообщение.
        
        Args:
            user_id: ID пользователя-получателя
            message: Словарь с данными для отправки
            
        Returns:
            bool: True если сообщение отправлено, False если пользователь не онлайн
        """
        if user_id in self.user_connections:
            return await self.send_message(self.user_connections[user_id], message)
        return False

    def get_connection_id_by_user(self, user_id: int) -> str | None:
        """
        Получение connection_id по user_id.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            str | None: connection_id или None если пользователь не онлайн
        """
        return self.user_connections.get(user_id)


# Глобальный синглтон менеджера соединений
# Используется во всём приложении для работы с WebSocket
manager = ConnectionManager()
