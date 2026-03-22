from fastapi import APIRouter

from routers.qr_router import router as qr_router


root_router = APIRouter(prefix="/api", tags=["API"])

routers = [
    qr_router,
]

for router in routers:
    root_router.include_router(router)
