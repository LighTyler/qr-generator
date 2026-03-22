"""
Экспорт роутеров FastAPI.

Этот модуль собирает все роутеры приложения в одном месте
для удобного импорта при настройке приложения.

Available routers:
    - root_router: Главный роутер, объединяющий все API роутеры
    - qr_router: Роутер для работы с QR-кодами
"""

from routers.root_router import root_router
from routers.qr_router import router as qr_router

__all__ = [
    "root_router",
    "qr_router",
]
