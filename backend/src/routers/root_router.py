"""
Главный роутер FastAPI приложения.

Объединяет все API роутеры под общим префиксом /api.
Это позволяет легко добавлять новые роутеры и управлять версионированием API.
"""

from fastapi import APIRouter

from routers.qr_router import router as qr_router


# Главный роутер с префиксом /api и тегом "API"
root_router = APIRouter(prefix="/api", tags=["API"])

# Список всех подключаемых роутеров
routers = [
    qr_router,  # Роутер для работы с QR-кодами
]

# Подключаем все роутеры к главному роутеру
for router in routers:
    root_router.include_router(router)
