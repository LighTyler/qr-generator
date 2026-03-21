from routers.dev_router import router as dev_router
from routers.user_router import router as user_router
from routers.root_router import root_router
from routers.qr_router import router as qr_router

__all__ = [
    "root_router",
    "qr_router",
]
