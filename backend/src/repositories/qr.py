from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.qr import QRRequest, QRResponse
from models.qr import QR


class QRRepositoryI(Protocol):
    async def create(self, qrdata: QRResponse) -> QR: ...
    async def get(self, qr_id: int) -> QR | None: ...
    async def get_by_email(self, email: str) -> QR | None: ...
    async def update(self, qrdata: QRResponse) -> QR: ...
    async def delete(self, qr_id: int): ...
    async def delete_by_email(self, email: str): ...

class QRRepository(QRRepositoryI):
    def __init__(
            self,
            session: AsyncSession,
        ):
            self.session = session
    async def create(self, qrdata: QRResponse) -> QR:
        qr = QR(**qrdata.model_dump()) 
        self.session.add(qr)
        await self.session.flush()
        await self.session.refresh(qr)
        return qr
    
    async def get(self, qr_id: int) -> QR | None:
        query = select(QR).where(QR.id == qr_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> QR | None:
        query = select(QR).where(QR.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update(self, qrdata: QRResponse) -> QR:
        # Ищем запись по email (уникальное поле)
        qr = await self.get_by_email(qrdata.email)
        if not qr:
            # Если запись не существует, создаём новую
            return await self.create(qrdata)
        
        # Обновляем только salt (другие поля не должны меняться)
        qr.salt = qrdata.salt
        
        await self.session.flush()
        await self.session.refresh(qr)
        return qr

    async def delete(self, qr_id: int) -> bool:
        qr = await self.get(qr_id)
        if not qr:
            return False
        await self.session.delete(qr)
        await self.session.flush()
        return True
    
    async def delete_by_email(self, email: str) -> bool:
        """Удалить QR запись по email пользователя"""
        qr = await self.get_by_email(email)
        if not qr:
            return False
        await self.session.delete(qr)
        await self.session.flush()
        return True